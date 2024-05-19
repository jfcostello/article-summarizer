# utils/rss_utils.py
# This module provides utility functions for parsing RSS feeds.

import feedparser

def parse_feed(feed_url):
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
