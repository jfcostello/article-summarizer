# scripts/main.py
#This script serves as the main entry point for an article summarization system. It utilizes a RedundancyManager to perform various tasks like fetching URLs, scraping content, summarizing articles, and tagging articles. The tasks can be executed individually based on command-line arguments or sequentially by default. The script logs the overall status and duration of the tasks performed. Celery_app calls this script with arguments as it's way of starting tasks and receiving their statuses

import sys
from redundancy_manager import RedundancyManager
from utils.logging_utils import log_status, log_duration
from datetime import datetime

# The main function that handles different tasks related to article processing
def main(task=None, run_all_scripts=False):
    # Initializes the redundancy manager with a configuration file
    manager = RedundancyManager('config/config.yaml')

    # Start time for overall duration logging
    overall_start_time = datetime.now()

    # Checks if the task is to fetch URLs, executes the task, and prints the result
    if task == "fetch_urls":
            total_new_urls = manager.execute_with_redundancy('fetch_urls')
            print(total_new_urls)
    # Checks if the task is to scrape content and executes the task
    elif task == "scrape_content":
        manager.execute_with_redundancy('scraper')
    # Checks if the task is to summarize articles and executes the task
    elif task == "summarize_articles":
        manager.execute_with_redundancy('summarizer')
    # Checks if the task is to tag articles and executes the task
    elif task == "tag_articles":
        manager.execute_with_redundancy('tagging')
    # If no specific task is given via an argument, all tasks are executed sequentially
    else:
        fetch_urls_status = manager.execute_with_redundancy('fetch_urls', run_all_scripts=run_all_scripts)
        scraper_status = manager.execute_with_redundancy('scraper', run_all_scripts=run_all_scripts)
        summarizer_status = manager.execute_with_redundancy('summarizer', run_all_scripts=run_all_scripts)
        tagging_status = manager.execute_with_redundancy('tagging', run_all_scripts=run_all_scripts)

        # Determines the overall status based on the status of individual tasks
        if all(status == "Success" for status in [fetch_urls_status, scraper_status, summarizer_status, tagging_status]):
            overall_status = "Success"
        elif any(status == "Error" for status in [fetch_urls_status, scraper_status, summarizer_status, tagging_status]):
            overall_status = "Error"
        else:
            overall_status = "Partial"

        # End time for overall duration logging
        overall_end_time = datetime.now()

        # Log the overall status and duration
        log_status("Redundancy Manager", [f"Overall run status: {overall_status}"], overall_status)
        log_duration("Redundancy Manager", overall_start_time, overall_end_time)

# Entry point of the script; it takes an optional task argument from the command line
if __name__ == "__main__":
    run_all_scripts = "runallscripts" in sys.argv  # Check for runallscripts argument
    task = sys.argv[1] if len(sys.argv) >= 2 else None  # Get task argument if provided

    main(task, run_all_scripts)  # Pass both task and run_all_scripts to main()


