import sys
from redundancy_manager import RedundancyManager
from utils.logging_utils import log_status, log_duration
from datetime import datetime

def main(task=None):
    manager = RedundancyManager('config/config.yaml')

    # Start time for overall duration logging
    overall_start_time = datetime.now()

    if task == "fetch_urls":
            total_new_urls = manager.execute_with_redundancy('fetch_urls')
            print(total_new_urls)
    elif task == "scrape_content":
        manager.execute_with_redundancy('scraper')
    elif task == "summarize_articles":
        manager.execute_with_redundancy('summarizer')
    elif task == "tag_articles":
        manager.execute_with_redundancy('tagging')
    else:
        # Execute all tasks sequentially
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

        # End time for overall duration logging
        overall_end_time = datetime.now()

        # Log the overall status and duration
        log_status("Redundancy Manager", [f"Overall run status: {overall_status}"], overall_status)
        log_duration("Redundancy Manager", overall_start_time, overall_end_time)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        task = sys.argv[1]
        main(task)
    else:
        main()