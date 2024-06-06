#!/root/.ssh/article-summarizer/as-env/bin/python3
# scripts/fetch_urls/fetch_urls_feedparser.py

import sys
import os
import feedparser 
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interfaces.url_fetcher import URLFetcher
from utils.url_fetch_utils import process_feeds

class FeedparserFetcher(URLFetcher):
    def fetch_and_store_urls(self):
        # Process feeds using the utility function and send script name for logging
        success = process_feeds(parse_feed=self.parse_feed, script_name=os.path.basename(__file__))
        return success

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
    success = fetcher.fetch_and_store_urls()
    print(success)  # Ensure this prints an integer
    sys.exit(0 if success else 1)