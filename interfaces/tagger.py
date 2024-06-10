# interfaces/tagger.py
# This module defines the Tagger interface for tagging summarized articles.

from abc import ABC, abstractmethod

class Tagger(ABC):
    """
    Interface for tagging summarized articles.
    Implement this interface to create custom taggers.
    """

    @abstractmethod
    def tag(self, summary):
        """
        Tag the given article summary.
        
        Args:
            summary (dict): The summarized article content to tag.
        
        Returns:
            dict: A dictionary containing tags and their relevancy scores.
        """
        pass
