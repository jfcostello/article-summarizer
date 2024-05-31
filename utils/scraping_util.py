# utils/scraping_utils.py
# This module provides utility functions for scraping and processing URLs.
# It includes functions to fetch URLs from the database, process each URL by scraping content,
# and log the status and duration of the scraping process.

from utils.db_utils import fetch_table_data, update_table_data
from utils.logging_utils import log_status, log_duration
from datetime import datetime
from task_management.celery_app import app

async def fetch_and_process_urls(table_name, fetch_condition, scraping_function, update_fields, script_name):
    start_time = datetime.now()
    log_entries = []
    total_items = 0
    failed_items = 0

    urls_to_scrape = fetch_table_data(table_name, fetch_condition)

    if not urls_to_scrape:
        log_entries.append({"message": "No URLs to process."})
        log_status(script_name, log_entries, 'Success')
        log_duration(script_name, start_time, datetime.now())
        return "Success"

    for record in urls_to_scrape:
        url = record['url']
        total_items += 1
        try:
            content = await scraping_function(url)
            update_data = {field: content for field in update_fields}
            update_data['scraped'] = True
            update_table_data(table_name, update_data, ('id', record['id']))
            log_entries.append({"message": f"Content updated successfully for URL {url}"})
        except Exception as e:
            log_entries.append({"message": f"Failed to scrape {url}: {str(e)}", "error": str(e)})
            failed_items += 1

    if failed_items == 0:
        log_status(script_name, log_entries, "Success")
        status = "Success"
    elif failed_items > 0 and failed_items < total_items:
        log_status(script_name, log_entries, "Partial")
        status = "Partial"
    else:
        log_status(script_name, log_entries, "Error")
        status = "Error"

    log_duration(script_name, start_time, datetime.now())
    return status

async def run_puppeteer_scraper(scraping_function, script_name):
    try:
        await fetch_and_process_urls(
            table_name='summarizer_flow',
            fetch_condition={'scraped': False},
            scraping_function=scraping_function,
            update_fields=['content'],
            script_name=script_name
        )
        return True  # Return True on success
    except Exception as e:
        log_status(script_name, [{"message": f"Exception during puppeteer scraping: {e}"}], "Error")
        return False  # Return False on exception
