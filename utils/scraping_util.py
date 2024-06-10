# utils/scraping_utils.py
# This module provides utility functions for scraping URLs and processing their content. It fetches URLs from a specified database table, processes each URL using a given scraping function, updates the database with the scraped content, and logs the status and duration of the scraping process..

from utils.db_utils import fetch_table_data, update_table_data
from utils.logging_utils import log_status, log_duration
from datetime import datetime
from task_management.celery_app import app

# Fetches URLs from a specified table, processes them by scraping content, and updates the table with the results.
async def fetch_and_process_urls(table_name, fetch_condition, scraping_function, update_fields, script_name):
    # Logs the start time and initializes log entries.
    start_time = datetime.now()
    log_entries = []
    total_items = 0
    failed_items = 0

    # Fetches URLs from the database based on the provided condition.
    urls_to_scrape = fetch_table_data(table_name, fetch_condition)

    # Checks if there are no URLs to process and logs the status.
    if not urls_to_scrape:
        log_entries.append({"message": "No URLs to process."})
        log_status(script_name, log_entries, 'Success')
        log_duration(script_name, start_time, datetime.now())
        return "Success"

    # Iterates over each URL, attempts to scrape content, and updates the database.
    for record in urls_to_scrape:
        # Extracts the URL from the record.
        url = record['url']
        total_items += 1
        try:
            # Attempts to scrape the content of the URL.
            content = await scraping_function(url)
            # Prepares the data to update in the database.
            update_data = {field: content for field in update_fields}
            # Marks the URL as scraped.
            update_data['scraped'] = True
            # Updates the table with the scraped content and logs success.
            update_table_data(table_name, update_data, ('id', record['id']))
            log_entries.append({"message": f"Content updated successfully for URL {url}"})
        # Catches any exceptions during scraping and logs the failure.
        except Exception as e:
            log_entries.append({"message": f"Failed to scrape {url}: {str(e)}", "error": str(e)})
            failed_items += 1

    # Determines the overall status based on the number of failed items and logs it.
    if failed_items == 0:
        log_status(script_name, log_entries, "Success")
        status = "Success"
    elif failed_items > 0 and failed_items < total_items:
        log_status(script_name, log_entries, "Partial")
        status = "Partial"
    else:
        log_status(script_name, log_entries, "Error")
        status = "Error"

    # Logs the duration of the scraping process.
    log_duration(script_name, start_time, datetime.now())
    return status

# Runs the puppeteer scraper by calling the fetch_and_process_urls function with specific parameters.
async def run_puppeteer_scraper(scraping_function, script_name):
    try:
        # Calls fetch_and_process_urls with specific parameters and returns True on success.
        await fetch_and_process_urls(
            table_name='summarizer_flow',
            fetch_condition={'scraped': False},
            scraping_function=scraping_function,
            update_fields=['content'],
            script_name=script_name
        )
        return True  # Return True on success
    # Catches any exceptions during the scraping process and logs them.
    except Exception as e:
        log_status(script_name, [{"message": f"Exception during puppeteer scraping: {e}"}], "Error")
        return False  # Return False on exception
