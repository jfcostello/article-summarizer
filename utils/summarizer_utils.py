# utils/summarizer_utils.py
# This module provides utility functions for summarizing articles. It includes functions for escaping quotes, extracting sections from content, and summarizing articles using different APIs. The summaries are then updated in a Supabase table.

import re
import json
import os
from datetime import datetime, timezone
from utils.db_utils import get_supabase_client, fetch_articles_with_logic
from utils.logging_utils import log_status, log_duration
from utils.llm_utils import call_llm_api
from config.config_loader import load_config
from task_management.celery_app import app

# Initialize Supabase client using environment variables
supabase = get_supabase_client()

def custom_escape_quotes(json_str):
    """
    Correctly escape quotes inside JSON string values, avoiding double escaping.
    
    Args:
        json_str (str): The JSON string to escape quotes in.
    
    Returns:
        str: The JSON string with correctly escaped quotes.
    """
    json_str = re.sub(r'(?<=: )"(.+?)"(?=,|\s*\})', lambda m: '"' + m.group(1).replace('"', '\\"') + '"', json_str)
    return json_str

def extract_section(content, start_key, end_key=None):
    """
    Extract text between start_key and optional end_key from content.
    
    Args:
        content (str): The content to extract the section from.
        start_key (str): The starting key to search for.
        end_key (str, optional): The ending key to search for. Defaults to None.
    
    Returns:
        str: The extracted section of text.
    """
    start_idx = content.find(start_key)
    if start_idx == -1:
        return ""  # start_key not found
    start_idx += len(start_key)
    if end_key:
        end_idx = content.find(end_key, start_idx)
        if end_idx == -1:
            end_idx = len(content)  # end_key not found, take until end
    else:
        end_idx = len(content)  # No end_key provided, take until end
    return content[start_idx:end_idx].strip()

def summarize_article(article_id, content, status_entries, systemPrompt, api_call_func):
    """
    Summarize an article using a specified API call function and update the 
    summarizer_flow table in Supabase.
    
    Args:
        article_id (int): The ID of the article to summarize.
        content (str): The content of the article to summarize.
        status_entries (list): List to store status messages.
        systemPrompt (str): The system prompt for the LLM.
        api_call_func (function): The function to call the specific LLM API.
    """
    try:
        # Get the parsed response content directly 
        response_content = api_call_func(content, systemPrompt) 

        # Extract sections 
        intro_paragraph = extract_section(response_content, "IntroParagraph:", "BulletPointSummary:")
        bullet_point_summary = extract_section(response_content, "BulletPointSummary:", "ConcludingParagraph:")
        bullet_point_summary = custom_escape_quotes(bullet_point_summary)

        try:
            json.loads(bullet_point_summary)  # Validate JSON
            valid_json = True
        except json.JSONDecodeError:
            valid_json = False
            bullet_point_summary = None
            status_entries.append({"message": f"Invalid JSON detected for BulletPointSummary in article ID {article_id}"})

        concluding_paragraph = extract_section(response_content, "ConcludingParagraph:")

        # Prepare data for update, always mark as summarized, but only update bulletpointsummary if json is valid
        update_data = {
            "IntroParagraph": intro_paragraph,
            "ConcludingParagraph": concluding_paragraph,
            "summarized": True  # Always mark as summarized
        }
        if valid_json:
            update_data["BulletPointSummary"] = bullet_point_summary

        # Perform the update
        supabase.table("summarizer_flow").update(update_data).eq("id", article_id).execute()

        status_entries.append({"message": f"Summary updated successfully for ID {article_id}"})

    except Exception as e:
        status_entries.append({"message": f"Error during summarization for ID {article_id}", "error": str(e)})

# Process articles for summarization and log the status and duration of the operation.
def process_articles(script_name, api_call_func=None):
    # Record the start time of the process.
    start_time = datetime.now(timezone.utc)
    status_entries = []
    total_items = 0
    failed_items = 0

    # Load configuration and fetch articles from the database.
    config = load_config()
    articles = fetch_articles_with_logic("summarizer_flow")
    system_prompt = config['systemPrompt']

    # If articles are found, summarize each one.
    if articles:
        for article in articles:
            total_items += 1
            summarize_article(article['id'], article['content'], status_entries, system_prompt, api_call_func)
            if "error" in status_entries[-1].keys():
                failed_items += 1
    else:
        status_entries.append({"message": "No articles to summarize"})
        
    # Log the status based on the number of failed items.
    if failed_items == 0:
        log_status(script_name, status_entries, "Success")
        task_status = "Success"
    elif failed_items > 0 and failed_items < total_items:
        log_status(script_name, status_entries, "Partial")
        task_status = "Partial"
    else:
        log_status(script_name, status_entries, "Error")
        task_status = "Error"

    # Log the duration of the script execution.
    log_duration(script_name, start_time, datetime.now(timezone.utc))

    return "Success" if failed_items == 0 else "Partial" if failed_items > 0 and failed_items < total_items else "Error"