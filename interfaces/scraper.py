#!/root/.ssh/article-summarizer/as-env/bin/python3
# interfaces/scraper.py
# This module defines the Scraper interface for scraping content from URLs.

from abc import ABC, abstractmethod

class Scraper(ABC):
    """
    Interface for scraping content from URLs.
    Implement this interface to create custom scrapers.
    """

    @abstractmethod
    def scrape(self, url):
        """
        Scrape content from the given URL.
        
        Args:
            url (str): The URL to scrape content from.
        
        Returns:
            str: The scraped content.
        """
        pass
