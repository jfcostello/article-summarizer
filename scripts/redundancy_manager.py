import sys
import os
import yaml
import logging
import subprocess
from datetime import datetime
from celery import Celery

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_utils import log_status, log_duration

app = Celery('tasks', broker='pyamqp://guest@localhost//')

class RedundancyManager:
    """
    A class to manage the execution of tasks with redundancy, running all implementations
    sequentially to ensure all work is handled.
    """
    def __init__(self, config_path):
        """
        Initialize the RedundancyManager with the given configuration path.
        
        Args:
            config_path (str): Path to the configuration file.
        """
        self.config = self.load_config(config_path)
        self.logger = logging.getLogger('redundancy_manager')
        logging.basicConfig(level=logging.INFO)

    def load_config(self, config_path):
        """
        Load the configuration from the given YAML file.
        
        Args:
            config_path (str): Path to the YAML configuration file.
        
        Returns:
            dict: Configuration dictionary loaded from the file.
        """
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def execute_with_redundancy(self, task_name, send_status=False, *args, **kwargs):
        """
        Execute all implementations of a task sequentially to ensure all work is handled.
        
        Args:
            task_name (str): Name of the task to be executed.
            send_status (bool): Whether to send statuses to Celery.
            *args: Variable length argument list for the task.
            **kwargs: Arbitrary keyword arguments for the task.
        
        Returns:
            int: The total count of new URLs added by all scripts.
        """
        task_config = self.config['interfaces'].get(task_name)
        if not task_config:
            self.logger.error(f"No configuration found for task: {task_name}")
            return 0
        
        implementations = [
            (task_config['primary'], True)
        ] + [(fallback, False) for fallback in task_config.get('fallbacks', [])]

        start_time = datetime.now()
        task_statuses = []
        total_new_urls = 0

        # Run all implementations sequentially
        for impl, is_primary in implementations:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), task_name, impl + ".py")
            result = execute_script(script_path)
            task_statuses.append(result)
            if isinstance(result, int):
                total_new_urls += result
                if result > 0:
                    self.logger.info(f"Script {impl} added {result} new URLs.")
            elif result == "Success":
                self.logger.info(f"Script {impl} executed successfully.")
            elif result == "Partial":
                self.logger.warning(f"Script {impl} returned partial success.")
            elif result == "Error":
                self.logger.error(f"Script {impl} failed.")

        # Determine the overall status of the task
        if "Error" in task_statuses:
            task_status = "Error"
        elif "Partial" in task_statuses:
            task_status = "Partial"
        else:
            task_status = "Success"

        end_time = datetime.now()
        log_status(task_name, task_statuses, task_status)
        log_duration(task_name, start_time, end_time)

        if send_status:
            app.send_task('tasks.update_status', args=[task_name, task_statuses, task_status])

        return total_new_urls

def execute_script(script_path):
    """
    Execute a script as a subprocess and capture its output.
    
    Args:
        script_path (str): The path to the script to be executed.
    
    Returns:
        str: "Success" if the script executed successfully, "Failure" if it failed.
    """
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        if result.stdout:
            logging.info(f"Script Output: {result.stdout.strip()}")
            try:
                new_url_count = int(result.stdout.strip())
                return new_url_count
            except ValueError:
                pass
        if result.stderr:
            logging.error(f"Script Error: {result.stderr.strip()}")
        
        if result.returncode == 0:
            return "Success"
        elif result.returncode == 2:
            return "Partial"
        else:
            logging.error(f"Script returned non-zero exit code: {result.returncode}")
            return "Error"
    except Exception as e:
        logging.error(f"Error executing script {script_path}: {e}")
        return "Error"

if __name__ == "__main__":
    # Create an instance of RedundancyManager with the path to the configuration file
    manager = RedundancyManager('config/config.yaml')
    
    # Execute fetch_urls task and aggregate the URL counts
    total_new_urls = manager.execute_with_redundancy('fetch_urls')
    
    # Log the total new URLs added
    log_status("fetch_urls", [f"Total new URLs added: {total_new_urls}"], "Success" if total_new_urls >= 0 else "Error")

    # Trigger the next tasks if new URLs were added
    if total_new_urls > 0:
        app.send_task('tasks.run_dependent_tasks')


