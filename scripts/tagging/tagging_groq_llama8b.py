#!/root/.ssh/article-summarizer/as-env/bin/python3
# /scripts/tagging/tagging_groq_llama8b.py
# This script tags summarized articles using Groq's API and stores the results in a Supabase database.
# It fetches articles needing tags, generates tags using a system prompt from a YAML configuration file,
# and logs the process and duration in Supabase.

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.tagging_utils import process_articles
from utils.llm_utils import call_llm_api

if __name__ == "__main__":
    process_articles(
        script_name=os.path.basename(__file__),
        primary=True,
        api_call_func=lambda content, systemPrompt: call_llm_api("llama3-8b-8192", content, systemPrompt, client_type="groq")
    )
