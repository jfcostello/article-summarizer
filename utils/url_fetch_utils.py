# utils/url_fetch_utils.py
# Utility functions for URL fetching and handling.

from utils.db_utils import fetch_table_data

def fetch_existing_urls(supabase, table_name, batch_size=1000):
    """
    Fetch existing URLs from the specified table in batches.
    
    Args:
        supabase (Client): The Supabase client.
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
    
    # print(f"New URLs: {new_urls_cleaned}")  # Debug statement
    # print(f"Deduplicated URLs: {deduplicated_urls}")  # Debug statement
    
    return deduplicated_urls

def insert_new_entries(supabase, table_name, new_entries, log_entries, batch_size=100):
    """
    Insert new entries into the specified table in batches.
    
    Args:
        supabase (Client): The Supabase client.
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

