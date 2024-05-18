#!/root/.ssh/article-summarizer/as-env/bin/python3
# This script fetches RSS feed URLs from a Supabase table (Musrt be marked as enabled), checks for new entries, and stores them in another table for further processing. 
# It logs the execution status and duration, handling errors and duplicates appropriately.
import os
import json
from datetime import datetime, timezone
import feedparser
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase setup using environment variables
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

def log_status(script_name, log_entry, status):
    """Logs the execution status and related messages for a given script in the 'log_script_status' table."""
    supabase.table("log_script_status").insert({
        "script_name": script_name,
        "log_entry": json.dumps(log_entry),  # Convert dictionary to JSON string
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status
    }).execute()

def log_duration(script_name, start_time, end_time):
    """Logs the duration of the script execution in the 'log_script_duration' table."""
    duration_seconds = (end_time - start_time).total_seconds()
    supabase.table("log_script_duration").insert({
        "script_name": script_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds
    }).execute()

def fetch_and_store_urls():
    """Fetches RSS feed URLs, checks for new entries, and stores them in the 'summarizer_flow' table. Logs status and duration."""
    start_time = datetime.now(timezone.utc)  # Start timing the script execution
    log_entries = []  # Initialize an empty list to collect log messages

    # Fetch enabled RSS feed URLs from the rss_feed_list table
    rss_feeds_response = supabase.table("rss_feed_list").select("rss_feed").eq("isEnabled", 'TRUE').execute()
    
    if not rss_feeds_response.data:
        # If no data is found or there is an error fetching RSS feed URLs, log the error and the duration, then return
        log_entries.append("Error fetching RSS feed URLs or no data found.")
        log_status("rss_scraper.py", {"messages": log_entries}, "Error")
        log_duration("rss_scraper.py", start_time, datetime.now(timezone.utc))
        return

    rss_feeds_data = rss_feeds_response.data
    for feed in rss_feeds_data:
        feed_url = feed['rss_feed']
        newsfeed = feedparser.parse(feed_url)
        existing_urls_response = supabase.table("summarizer_flow").select("url").execute()

        if existing_urls_response.data is None:
            # If fetching existing URLs fails, log the error and continue to the next feed
            log_entries.append(f"Failed to fetch existing URLs for {feed_url}.")
            continue

        existing_urls = {item['url'] for item in existing_urls_response.data}
        new_entries = []
        for entry in newsfeed.entries:
            if entry.get('link') and entry.get('link') not in existing_urls:
                # If the entry has a link and it is not already in the existing URLs, create a new entry dictionary
                new_entry = {
                    'url': entry.get('link'),
                    'ArticleTitle': entry.get('title', 'No Title Provided'),
                    'scraped': False
                }
                new_entries.append(new_entry)

        if new_entries:
         # If there are new entries, try to insert them into the 'summarizer_flow' table
            for entry in new_entries:
                try:
                    insert_response = supabase.table("summarizer_flow").insert(entry).execute()
                    if insert_response.data is None:
                       log_entries.append(f"Failed to insert data for {entry['url']}.")
                    else:
                        log_entries.append(f"Data inserted successfully for {entry['url']}.")
                except Exception as e:
                    if "duplicate key value violates unique constraint" in str(e):
                         # If insertion fails due to duplicate URL, log the duplicate URL message
                         log_entries.append(f"Duplicate URL found: {entry['url']}. Skipping insertion.")
                    else:
                         # If insertion fails due to other reasons, log the error
                        log_entries.append(f"Error inserting data for {entry['url']}: {str(e)}")
        else:
            # If there are no new entries, log that no new URLs were added for this feed URL
             log_entries.append(f"No new URLs to add for {feed_url}.")

    # Log the successful completion of the script with collected messages
    log_status("rss_scraper.py", {"messages": log_entries}, "Success")
    # Record and log the duration of the script execution
    log_duration("rss_scraper.py", start_time, datetime.now(timezone.utc))

if __name__ == "__main__":
    fetch_and_store_urls()
