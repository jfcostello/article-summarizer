#!/root/.ssh/article-summarizer/as-env/bin/python3
# interfaces/summarizer.py
# This module defines the Summarizer interface for summarizing article content.

from abc import ABC, abstractmethod

class Summarizer(ABC):
    """
    Interface for summarizing article content.
    Implement this interface to create custom summarizers.
    """

    @abstractmethod
    def summarize(self, content):
        """
        Summarize the given article content.
        
        Args:
            content (str): The article content to summarize.
        
        Returns:
            dict: A dictionary containing the summary parts (intro, bullet points, conclusion).
        """
        pass
