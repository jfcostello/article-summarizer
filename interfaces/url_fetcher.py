# interfaces/url_fetcher.py
# This module defines the URLFetcher interface for fetching URLs.

from abc import ABC, abstractmethod

class URLFetcher(ABC):
    """
    Interface for fetching URLs.
    Implement this interface to create custom URL fetchers.
    """

    @abstractmethod
    def fetch_and_store_urls(self):
        """
        Fetch and store URLs.
        
        Returns:
            None
        """
        pass
