# scripts/fetch_urls/fetch_urls_feedparser.py
# This script fetches RSS feed URLs from a Supabase table (must be marked as enabled), checks for new entries,
# and stores them in another table for further processing. It logs the execution status and duration,
# handling errors and duplicates appropriately.

import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interfaces.url_fetcher import URLFetcher
from utils.db_utils import get_supabase_client, fetch_feed_urls
from utils.logging_utils import log_status, log_duration
from utils.url_fetch_utils import fetch_existing_urls, deduplicate_urls, insert_new_entries
from utils.rss_utils import parse_feed

# Load environment variables from the .env file
load_dotenv()

class FeedparserFetcher(URLFetcher):
    def __init__(self):
        self.supabase = get_supabase_client()

    def fetch_and_store_urls(self):
        start_time = datetime.now(timezone.utc)
        log_entries = []

        # Fetch enabled RSS feed URLs from the rss_feed_list table
        rss_feeds_response = fetch_feed_urls()
        
        if not rss_feeds_response:
            log_entries.append("Error fetching RSS feed URLs or no data found.")
            log_status("fetch_urls_feedparser.py", {"messages": log_entries}, "Error")
            log_duration("fetch_urls_feedparser.py", start_time, datetime.now(timezone.utc))
            return

        for feed in rss_feeds_response:
            feed_url = feed['rss_feed']
            new_entries = parse_feed(feed_url)
            existing_urls = fetch_existing_urls(self.supabase, "summarizer_flow")

            # print(f"Existing URLs: {existing_urls}")  # Debug statement
            # print(f"New Entries: {new_entries}")  # Debug statement

            deduplicated_entries = deduplicate_urls(new_entries, existing_urls)

            # print(f"Deduplicated Entries: {deduplicated_entries}")  # Debug statement

            if deduplicated_entries:
                insert_new_entries(self.supabase, "summarizer_flow", deduplicated_entries, log_entries)
            else:
                log_entries.append(f"No new URLs to add for {feed_url}.")

        log_status("fetch_urls_feedparser.py", {"messages": log_entries}, "Success")
        log_duration("fetch_urls_feedparser.py", start_time, datetime.now(timezone.utc))

if __name__ == "__main__":
    fetcher = FeedparserFetcher()
    fetcher.fetch_and_store_urls()
