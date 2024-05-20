# scripts/fetch_urls/fetch_urls_feedparser.py
# This script fetches RSS feed URLs from a Supabase table (must be marked as enabled), checks for new entries,
# and stores them in another table for further processing. It logs the execution status and duration,
# handling errors and duplicates appropriately.

import sys
import os
from datetime import datetime, timezone
import feedparser 
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interfaces.url_fetcher import URLFetcher
from utils.url_fetch_utils import process_feeds

class FeedparserFetcher(URLFetcher):
    def fetch_and_store_urls(self):
        # Initialize start time and log entries
        start_time = datetime.now(timezone.utc)
        log_entries = []

        # Process feeds using the utility function
        process_feeds(log_entries=log_entries, start_time=start_time, parse_feed=self.parse_feed)

    def parse_feed(self, feed_url):
        """
        Parse an RSS feed URL to extract entries.

        Args:
            feed_url (str): The URL of the RSS feed to be parsed.

        Returns:
            list: A list of entries from the RSS feed.
        """
        newsfeed = feedparser.parse(feed_url)
        entries = [
            {
                'url': entry.get('link'),
                'ArticleTitle': entry.get('title', 'No Title Provided'),
                'scraped': False
            }
            for entry in newsfeed.entries if entry.get('link')
        ]
        return entries

if __name__ == "__main__":
    fetcher = FeedparserFetcher()
    fetcher.fetch_and_store_urls()
