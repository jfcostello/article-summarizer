#!/root/.ssh/article-summarizer/as-env/bin/python3
# /scripts/summarizer/summarizer_groq_llama8b.py
# This script fetches articles from the Supabase database that have been scraped but not yet summarized,
# uses the Groq API to generate summaries, and updates the database with the summaries. It logs both the
# status and duration of the summarization process.

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.summarizer_utils import process_articles
from utils.llm_utils import call_llm_api

if __name__ == "__main__":
    process_articles(
        script_name=os.path.basename(__file__),
        primary=True,
        api_call_func=lambda content, systemPrompt: call_llm_api("llama3-8b-8192", content, systemPrompt, client_type="groq")
    )