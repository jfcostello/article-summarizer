# utils/url_fetch_utils.py
# This file provides utility functions for fetching and handling URLs, specifically for processing RSS feeds (Or other sources which may be added later) and updating a database with new entries. It includes functions for fetching existing URLs from a database, deduplicating new URLs, inserting new entries, and processing feeds with logging and error handling.

from utils.logging_utils import log_status, log_duration
from datetime import datetime, timezone
from utils.db_utils import get_supabase_client, fetch_table_data, update_table_data
from config.config_loader import load_config

config = load_config()
table_names = config.get('tables', {})

# Initialize Supabase client using environment variables
supabase = get_supabase_client()

def fetch_existing_urls(batch_size=1000):
    """
    Fetch existing URLs from the specified table in batches.
    
    Args:
        batch_size (int): The number of records to fetch per batch.
    
    Returns:
        set: A set of existing URLs.
    """
    existing_urls = set()
    existing_urls_response = supabase.table(table_names['summarizer_flow']).select("url").order("created_at", desc=True).limit(batch_size).execute()
    if existing_urls_response.data:
        existing_urls = {item['url'].strip() for item in existing_urls_response.data}
    
    return existing_urls

def deduplicate_urls(new_urls, existing_urls):
    """
    Remove URLs that already exist in the existing URLs set.
    
    Args:
        new_urls (list): List of new URLs to be checked.
        existing_urls (set): Set of existing URLs.
    
    Returns:
        list: A list of deduplicated URLs.
    """
    new_urls_cleaned = [{**url, 'url': url['url'].strip()} for url in new_urls]  # Ensure URLs are trimmed
    deduplicated_urls = [url for url in new_urls_cleaned if url['url'] not in existing_urls]
    
    return deduplicated_urls   

def insert_new_entries(table_name, new_entries, log_entries):
    """
    Insert new entries into the specified table one by one.
    
    Args:
        table_name (str): The name of the table to insert entries into.
        new_entries (list): List of new entries to be inserted.
        log_entries (list): List to store log entries.
    """
    inserted_count = 0
    for entry in new_entries:
        try:
            insert_response = supabase.table(table_name).insert(entry).execute()
            if insert_response.data:  # Check if data was actually inserted
                inserted_count += 1
                log_entries.append(f"Data inserted successfully for {entry['url']}.")
            else:
                log_entries.append(f"No data inserted for {entry['url']}. Response: {insert_response}")
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                log_entries.append(f"Duplicate URL rejected by Supabase: {entry['url']}. Skipping insertion.")
            else:
                log_entries.append(f"Error inserting data for {entry['url']}: {str(e)}")
    return inserted_count

# Processes RSS feeds by fetching enabled feeds from the database, parsing them, deduplicating new entries, and inserting them into the specified table. Logs the process and returns the total count of new URLs added.
def process_feeds(table_name="summarizer_flow", parse_feed=None, script_name="script", app=None):
    # Records the start time for the feed processing.
    start_time = datetime.now(timezone.utc)
    # Initializes the log entries list and counters for total items, failed items, and new URLs.
    log_entries = []
    total_items = 0
    failed_items = 0
    total_new_urls = 0

    # Checks if the parse_feed function is provided, raising an error if not.
    if parse_feed is None:
        raise ValueError("A parse_feed function must be provided")

    # Tries to fetch the RSS feed URLs from the database.
    try:
        rss_feeds_response = fetch_table_data("rss_feed_list", {"isEnabled": 'TRUE'})

        # Logs an error if no data is found.
        if not rss_feeds_response:
            log_entries.append("Error fetching RSS feed URLs or no data found.")
            log_status(script_name, {"messages": log_entries}, "Error")
            log_duration(script_name, start_time, datetime.now(timezone.utc))
            return 0

        # Iterates over each feed in the response.
        for feed in rss_feeds_response:
            feed_url = feed['rss_feed']
            new_entries = parse_feed(feed_url)
            # Parses the feed URL to get new entries and updates the total item count.
            total_items += len(new_entries)
            # Fetches existing URLs and deduplicates the new entries.
            existing_urls = fetch_existing_urls()
            deduplicated_entries = deduplicate_urls(new_entries, existing_urls)

            # Inserts the deduplicated entries into the database.
            if deduplicated_entries:
                new_url_count = insert_new_entries(table_name, deduplicated_entries, log_entries)
                total_new_urls += new_url_count
                # Log "New entry added" ONLY if insertion was successful:
                for entry in deduplicated_entries:
                    if any(f"Data inserted successfully for {entry['url']}" in log for log in log_entries):
                        log_entries.append(f"New entry added: {entry['url']}") 
            else:
                log_entries.append(f"No new URLs to add for {feed_url}.")

        # Logs the overall status based on the count of failed items.
        if failed_items == 0:
            log_status(script_name, {"messages": log_entries}, "Success")
        elif failed_items > 0 and failed_items < total_items:
            log_status(script_name, {"messages": log_entries}, "Partial")
        else:
            log_status(script_name, {"messages": log_entries}, "Error")

        # Logs the duration of the feed processing.
        log_duration(script_name, start_time, datetime.now(timezone.utc))
        return total_new_urls

    # Handles and logs any exceptions that occur during the process.
    except Exception as e:
        log_entries.append(f"Exception during feed processing: {e}")
        log_status(script_name, {"messages": log_entries}, "Error")
        log_duration(script_name, start_time, datetime.now(timezone.utc))
        return 0
