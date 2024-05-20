#!/root/.ssh/article-summarizer/as-env/bin/python3
# scripts/summarizer/summarizer_groq_llama8b.py
# This script fetches articles from the Supabase database that have been scraped but not yet summarized,
# uses the Groq API to generate summaries, and updates the database with the summaries. It logs both the
# status and duration of the summarization process.

import sys
import os
from datetime import datetime, timezone
from groq import Groq

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.summarizer_utils import summarize_article
from config.config_loader import load_config
from utils.logging_utils import log_status, log_duration
from utils.db_utils import fetch_table_data

# Initialize Groq client using environment variables
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_groq_api(content, systemPrompt):
    """
    Call the Groq API to summarize the content.
    
    Args:
        content (str): The content to summarize.
        systemPrompt (str): The system prompt for the LLM.
    
    Returns:
        str: The response content from the Groq API.
    """
    chat_completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        max_tokens=4000,
        temperature=0,
        messages=[
            {"role": "user", "content": content},
            {"role": "system", "content": systemPrompt}
        ]
    )
    return chat_completion.choices[0].message.content

def main():
    # Record the start time of the script
    start_time = datetime.now(timezone.utc)
    
    # Load configuration from config.yaml and .env
    config = load_config()
    
    articles = fetch_table_data("summarizer_flow", {"scraped": True, "summarized": False})
    
    # Initialize a list to store status messages
    status_entries = []
    
    # Get the system prompt from the configuration
    system_prompt = config['systemPrompt']

    # If there are articles to summarize, process each one
    if articles:
        for article in articles:
            summarize_article(article['id'], article['content'], status_entries, system_prompt, call_groq_api)
    else:
        # If no articles to summarize, log that information
        status_entries.append({"message": "No articles to summarize"})

    # Record the end time of the script
    end_time = datetime.now(timezone.utc)
    
    # Log the duration of the script
    log_duration("summarizer_groq_llama8b.py", start_time, end_time)
    
    # Log the status of the script
    log_status("summarizer_groq_llama8b.py", status_entries, "Complete")

if __name__ == "__main__":
    main()
