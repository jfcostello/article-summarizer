import sys
from redundancy_manager import RedundancyManager
from utils.logging_utils import log_status, log_duration
from datetime import datetime

def main(task=None, send_status=False):
    manager = RedundancyManager('config/config.yaml')

    # Start time for overall duration logging
    overall_start_time = datetime.now()

    if task == "fetch_urls":
        manager.execute_with_redundancy('fetch_urls', send_status)
    elif task == "scrape_content":
        manager.execute_with_redundancy('scraper', send_status)
    elif task == "summarize_articles":
        manager.execute_with_redundancy('summarizer', send_status)
    elif task == "tag_articles":
        manager.execute_with_redundancy('tagging', send_status)
    else:
        # Execute all tasks sequentially
        fetch_urls_status = manager.execute_with_redundancy('fetch_urls', send_status)
        scraper_status = manager.execute_with_redundancy('scraper', send_status)
        summarizer_status = manager.execute_with_redundancy('summarizer', send_status)
        tagging_status = manager.execute_with_redundancy('tagging', send_status)

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
    if len(sys.argv) == 3:
        task = sys.argv[1]
        send_status = sys.argv[2].lower() == 'true'
        main(task, send_status)
    elif len(sys.argv) == 2:
        task = sys.argv[1]
        main(task)
    else:
        main()
