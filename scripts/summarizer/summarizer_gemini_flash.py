# scripts/summarizer/summarizer_gemini_pro.py
# This script fetches articles from the Supabase database that have been scraped but not yet summarized,
# uses the Gemini API to generate summaries, and updates the database with the summaries. It logs both the
# status and duration of the summarization process.

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.summarizer_utils import process_articles
from utils.llm_utils import call_llm_api

if __name__ == "__main__":
    success = process_articles(
        script_name=os.path.basename(__file__),
        api_call_func=lambda content, systemPrompt: call_llm_api(
            "gemini-1.5-flash",
            content, 
            systemPrompt, 
            client_type="gemini",
            max_tokens=8192  # Set the max tokens to 8192
        )
    )
    sys.exit(0 if success else 1)