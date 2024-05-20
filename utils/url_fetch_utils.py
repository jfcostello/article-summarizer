# utils/url_fetch_utils.py
# Utility functions for URL fetching and handling.

from utils.logging_utils import log_status, log_duration
from datetime import datetime, timezone
from utils.db_utils import get_supabase_client, fetch_table_data, update_table_data  

# Initialize Supabase client using environment variables
supabase = get_supabase_client()

def fetch_existing_urls(table_name, batch_size=1000):
    """
    Fetch existing URLs from the specified table in batches.
    
    Args:
        table_name (str): The name of the table to fetch URLs from.
        batch_size (int): The number of records to fetch per batch.
    
    Returns:
        set: A set of existing URLs.
    """
    existing_urls = set()
    offset = 0

    while True:
        existing_urls_response = supabase.table(table_name).select("url").range(offset, offset + batch_size - 1).execute()
        if not existing_urls_response.data:
            break
        
        batch_urls = {item['url'].strip() for item in existing_urls_response.data}
        existing_urls.update(batch_urls)
        offset += batch_size

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

def insert_new_entries(table_name, new_entries, log_entries, batch_size=100):
    """
    Insert new entries into the specified table in batches.
    
    Args:
        table_name (str): The name of the table to insert entries into.
        new_entries (list): List of new entries to be inserted.
        log_entries (list): List to store log entries.
        batch_size (int): The number of records to insert per batch.
    """
    for i in range(0, len(new_entries), batch_size):
        batch = new_entries[i:i + batch_size]
        try:
            insert_response = supabase.table(table_name).insert(batch).execute()
            if insert_response.data:
                for entry in batch:
                    log_entries.append(f"Data inserted successfully for {entry['url']}.")
            else:
                for entry in batch:
                    log_entries.append(f"Failed to insert data for {entry['url']}.")
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                for entry in batch:
                    if entry['url'] in str(e):
                        log_entries.append(f"Duplicate URL detected by Supabase: {entry['url']}. Skipping insertion.")
            else:
                for entry in batch:
                    log_entries.append(f"Error inserting data for {entry['url']}: {str(e)}")
    
    # Log the results of the insertion
    for log_entry in log_entries:
        print(log_entry)  # Replace this with actual logging if necessary

def process_feeds(table_name="summarizer_flow", parse_feed=None):
    """
    Process the RSS feeds: fetch, parse, deduplicate, and insert new entries.
    
    Args:
        table_name (str): The name of the table to fetch and insert URLs. Defaults to "summarizer_flow".
        parse_feed (function): The function to parse the RSS feed. Must be provided.
    """
    start_time = datetime.now(timezone.utc)  # Initialize start time internally
    log_entries = []  # Initialize log entries internally

    if parse_feed is None:
        raise ValueError("A parse_feed function must be provided")

    # Fetch enabled RSS feed URLs from the rss_feed_list table
    rss_feeds_response = fetch_table_data("rss_feed_list", {"isEnabled": 'TRUE'})

    if not rss_feeds_response:
        log_entries.append("Error fetching RSS feed URLs or no data found.")
        log_status("fetch_urls_feedparser.py", {"messages": log_entries}, "Error")
        log_duration("fetch_urls_feedparser.py", start_time, datetime.now(timezone.utc))
        return

    for feed in rss_feeds_response:
        feed_url = feed['rss_feed']
        new_entries = parse_feed(feed_url)
        existing_urls = fetch_table_data(table_name, {"scraped": False})

        deduplicated_entries = [entry for entry in new_entries if entry['url'] not in {url['url'] for url in existing_urls}]

        if deduplicated_entries:
            update_table_data(table_name, deduplicated_entries, ('url', 'scraped'))
            log_entries.append(f"New entries added for {feed_url}.")
        else:
            log_entries.append(f"No new URLs to add for {feed_url}.")

    log_status("fetch_urls_feedparser.py", {"messages": log_entries}, "Success")
    log_duration("fetch_urls_feedparser.py", start_time, datetime.now(timezone.utc))