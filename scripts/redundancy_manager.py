# scripts/redundancy_manager.py
# This script manages the execution of tasks with redundancy.
# The execute_script function has been updated to use a subprocess timeout (with a 300-second limit)
# and to kill the process group if the script exceeds that timeout.
import sys
import os
import yaml
import logging
import subprocess
import signal
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
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def execute_with_redundancy(self, task_name, send_status=False, run_all_scripts=False, *args, **kwargs):
        """
        Execute all implementations of a task sequentially, running fallbacks only if 
        the previous implementation did not return a status of "Success"
        Any other status, or no status, results in the next script running.
        If Success is returned, it runs no further scripts.
        If run_all_scripts arg is given, it runs all scripts back to back regardless of status.

        Args:
            task_name (str): Name of the task to be executed.
            send_status (bool): Whether to send statuses to Celery.
            run_all_scripts (bool): If True, run all scripts regardless of status.
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

        # Run implementations sequentially
        for impl, is_primary in implementations:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", task_name, impl + ".py")

            # Execute the script and capture the status
            result = execute_script(script_path)
            task_statuses.append(result)

            # Handle URL counts (for fetch_urls task)
            if isinstance(result, int):
                total_new_urls += result
                if result > 0:
                    self.logger.info(f"Script {impl} added {result} new URLs.")

            # Log script status
            elif result == "Success":
                self.logger.info(f"Script {impl} executed successfully.")
            elif result == "Partial":
                self.logger.warning(f"Script {impl} returned partial success.")
            elif result == "Error":
                self.logger.error(f"Script {impl} failed.")
            else:  # Handle cases where no status is returned or an unexpected status
                self.logger.error(f"Script {impl} returned an unexpected status or no status: {result}")

            # Conditional break based on status and run_all_scripts flag
            if not run_all_scripts and result == "Success":
                # Skip remaining implementations for this task ONLY if run_all_scripts is False
                break

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
        str: "Success" if the script executed successfully, or a URL count if applicable.
    """
    try:
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        try:
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            stdout, stderr = process.communicate()
            logging.error(f"Script timed out: {script_path}")
            return "Error"
        if stdout:
            logging.info(f"Script Output: {stdout.strip()}")
            try:
                new_url_count = int(stdout.strip())
                return new_url_count
            except ValueError:
                pass
        if stderr:
            logging.error(f"Script Error: {stderr.strip()}")
        
        if process.returncode == 0:
            return "Success"
        elif process.returncode == 2:
            return "Partial"
        else:
            logging.error(f"Script returned non-zero exit code: {process.returncode}")
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
