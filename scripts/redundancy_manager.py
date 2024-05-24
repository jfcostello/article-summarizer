# scripts/redundancy_manager.py

import sys
import os
import yaml
import logging
import subprocess
from datetime import datetime

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_utils import log_status, log_duration

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

    def execute_with_redundancy(self, task_name, *args, **kwargs):
        """
        Execute all implementations of a task sequentially to ensure all work is handled.
        
        Args:
            task_name (str): Name of the task to be executed.
            *args: Variable length argument list for the task.
            **kwargs: Arbitrary keyword arguments for the task.
        
        Returns:
            str: The overall status of the task execution ("Success", "Partial", or "Error").
        """
        task_config = self.config['interfaces'].get(task_name)
        if not task_config:
            self.logger.error(f"No configuration found for task: {task_name}")
            return "Error"
        
        implementations = [
            (task_config['primary'], True)
        ] + [(fallback, False) for fallback in task_config.get('fallbacks', [])]

        start_time = datetime.now()
        task_status = "Success"

        # Run all implementations sequentially
        for impl, is_primary in implementations:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), task_name, impl + ".py")
            result = self.execute_script(script_path)
            if result == "Partial":
                task_status = "Partial"
                self.logger.warning(f"Script {impl} returned partial success.")
            elif result == "Error":
                task_status = "Error"
                self.logger.error(f"Script {impl} failed.")

        end_time = datetime.now()
        log_duration(task_name, start_time, end_time)

        return task_status

    def execute_script(self, script_path):
        """
        Execute a script as a subprocess and capture its output.
        
        Args:
            script_path (str): The path to the script to be executed.
        
        Returns:
            str: "Success" if the script executed successfully, "Error" if it failed,
                 or "Partial" if it returned a partial success.
        """
        try:
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
            self.logger.info(f"Script Output: {result.stdout}")
            self.logger.error(f"Script Error: {result.stderr}")
            if result.returncode == 0:
                return "Success"
            elif result.returncode == 2:
                return "Partial"
            else:
                self.logger.error(f"Script returned non-zero exit code: {result.returncode}")
                return "Error"
        except Exception as e:
            self.logger.error(f"Error executing script {script_path}: {e}")
            return "Error"

if __name__ == "__main__":
    # Create an instance of RedundancyManager with the path to the configuration file
    manager = RedundancyManager('config/config.yaml')
    
    # Execute tasks with redundancy logic
    fetch_urls_status = manager.execute_with_redundancy('fetch_urls')
    scraper_status = manager.execute_with_redundancy('scraper')
    summarizer_status = manager.execute_with_redundancy('summarizer')
    tagging_status = manager.execute_with_redundancy('tagging')

    # Determine the overall status of the run
    if all(status == "Success" for status in [fetch_urls_status, scraper_status, summarizer_status, tagging_status]):
        overall_status = "Success"
    elif any(status == "Error" for status in [fetch_urls_status, scraper_status, summarizer_status, tagging_status]):
        overall_status = "Error"
    else:
        overall_status = "Partial"

    # Log the overall status of the run
    log_status("Redundancy Manager", [f"Overall run status: {overall_status}"], overall_status)