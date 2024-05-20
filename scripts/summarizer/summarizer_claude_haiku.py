#!/root/.ssh/article-summarizer/as-env/bin/python3
# scripts/summarizer/summarize_claude_haiku.py
# This script fetches articles from the Supabase database that have been scraped but not yet summarized,
# or have missing summary sections, uses the Anthropics API to generate summaries, and updates the database
# with the summaries. It logs both the status and duration of the summarization process.

import sys
import os
from datetime import datetime, timezone
import anthropic

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.summarizer_utils import summarize_article
from config.config_loader import load_config
from utils.logging_utils import log_status, log_duration
from utils.db_utils import fetch_table_data

# Initialize Anthropics client using environment variables
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def call_anthropic_api(content, systemPrompt):
    """
    Call the Anthropics API to summarize the content.
    
    Args:
        content (str): The content to summarize.
        systemPrompt (str): The system prompt for the LLM.
    
    Returns:
        str: The response content from the Anthropics API.
    """
    chat_completion = anthropic_client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4000,
        temperature=0,
        system=systemPrompt,
        messages=[{"role": "user", "content": content}]
    )
    if chat_completion.content and isinstance(chat_completion.content, list):
        structured_text = getattr(chat_completion.content[0], 'text', None)
        if structured_text:
            return structured_text
        else:
            raise ValueError("Text attribute not found in response")
    else:
        raise ValueError("Invalid response format or empty content")

def main():
    # Record the start time of the script
    start_time = datetime.now(timezone.utc)
    
    # Load configuration from config.yaml and .env
    config = load_config()
    
    # Define the custom complex filters for fetching articles
    complex_filters = "summarized.eq.false,IntroParagraph.is.null,IntroParagraph.eq.,BulletPointSummary.is.null,BulletPointSummary.eq.,ConcludingParagraph.is.null,ConcludingParagraph.eq."
    
    # Fetch articles that have been scraped but not yet summarized, or have missing summary sections
    articles = fetch_table_data("summarizer_flow", {"scraped": True}, complex_filters)
    
    # Initialize a list to store status messages
    status_entries = []
    
    # Get the system prompt from the configuration
    system_prompt = config['systemPrompt']

    # If there are articles to summarize, process each one
    if articles:
        for article in articles:
            summarize_article(article['id'], article['content'], status_entries, system_prompt, call_anthropic_api)
    else:
        # If no articles to summarize, log that information
        status_entries.append({"message": "No articles to summarize"})

    # Record the end time of the script
    end_time = datetime.now(timezone.utc)
    
    # Log the duration of the script
    log_duration("summarize_claude_haiku.py", start_time, end_time)
    
    # Log the status of the script
    log_status("summarize_claude_haiku.py", status_entries, "Complete")

if __name__ == "__main__":
    main()
