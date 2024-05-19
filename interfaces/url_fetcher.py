# interfaces/url_fetcher.py
# This module defines the URLFetcher interface for fetching URLs from various sources.

from abc import ABC, abstractmethod

class URLFetcher(ABC):
    """
    Interface for fetching URLs.
    Implement this interface to create custom URL fetchers.
    """

    @abstractmethod
    def fetch_urls(self):
        """
        Fetch URLs from a source.
        
        Returns:
            list: A list of URLs.
        """
        pass
