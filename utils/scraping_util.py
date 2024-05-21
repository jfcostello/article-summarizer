# utils/scraping_utils.py
# This module provides utility functions for scraping and processing URLs.
# It includes functions to fetch URLs from the database, process each URL by scraping content,
# and log the status and duration of the scraping process.

from utils.db_utils import fetch_table_data, update_table_data
from utils.logging_utils import log_status, log_duration
from datetime import datetime

async def fetch_and_process_urls(table_name, fetch_condition, scraping_function, update_fields, script_name):
    """
    Fetch URLs from the specified table, process each URL by scraping content,
    and update the database with the scraped content.
    
    Args:
        table_name (str): The name of the table to fetch URLs from.
        fetch_condition (dict): The condition to filter URLs to be fetched.
        scraping_function (function): The function to scrape content from a URL.
        update_fields (list): The fields to update in the table with the scraped content.
        script_name (str): The name of the script for logging purposes.
    """
    start_time = datetime.now()
    log_entries = []

    # Fetch URLs to be scraped
    urls_to_scrape = fetch_table_data(table_name, fetch_condition)

    if not urls_to_scrape:
        log_entries.append({"message": "No URLs to process."})
        log_status(script_name, log_entries, 'No URLs')
        log_duration(script_name, start_time, datetime.now())
        return

    # Process each URL
    for record in urls_to_scrape:
        url = record['url']
        try:
            content = await scraping_function(url)  # Ensure the coroutine is awaited
            update_data = {field: content for field in update_fields}
            update_data['scraped'] = True
            update_table_data(table_name, update_data, ('id', record['id']))
            log_entries.append({"message": f"Content updated successfully for URL {url}"})
        except Exception as e:
            log_entries.append({"message": f"Failed to scrape {url}: {str(e)}", "error": str(e)})

    end_time = datetime.now()
    log_status(script_name, log_entries, 'Complete')
    log_duration(script_name, start_time, end_time)

async def run_puppeteer_scraper(scraping_function, script_name):
    """
    Run the Puppeteer scraping process for all URLs that need to be scraped.
    
    Args:
        scraping_function (function): The function to scrape content from a URL.
        script_name (str): The name of the script for logging purposes.
    """
    await fetch_and_process_urls(
        table_name='summarizer_flow',
        fetch_condition={'scraped': False},
        scraping_function=scraping_function,
        update_fields=['content'],
        script_name=script_name
    )
