#!/root/.ssh/article-summarizer/as-env/bin/python3
## /scripts/tagging/tagging_groq_llama8b.py
# This script tags summarized articles using Groq's API and stores the results in a Supabase database.
# It fetches articles needing tags, generates tags using a system prompt from a YAML configuration file,
# and logs the process and duration in Supabase.

import sys
import os
from datetime import datetime, timezone

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import utility functions and modules
from utils.tagging_utils import construct_system_prompt, fetch_articles, process_tags, process_articles
from utils.logging_utils import log_status, log_duration
from groq import Groq

# Initialize Groq client using environment variable for API key
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Define script_name globally
script_name = "tagging_groq_llama8b.py"

# Generate tags for an article using Groq's API
def generate_tags(article_id, content, system_prompt, status_entries):
    chat_completion = client.chat.completions.create(
        model="llama3-8b-8192",
        max_tokens=4000,
        temperature=0,
        messages=[
            {"role": "user", "content": content},
            {"role": "system", "content": system_prompt}
        ]
    )

    # Process tags and update the database
    result = process_tags(article_id, chat_completion, status_entries)
    return result

# Main function to fetch articles, generate tags, and log the process
def main():
    start_time = datetime.now(timezone.utc)
    status_entries = []

    # Construct the system prompt
    system_prompt = construct_system_prompt()

    # Fetch articles
    articles = fetch_articles()

    # Process articles
    process_articles(articles, system_prompt, status_entries, generate_tags)

    end_time = datetime.now(timezone.utc)
    log_duration(script_name, start_time, end_time)
    log_status(script_name, status_entries, "Complete")

if __name__ == "__main__":
    main()
