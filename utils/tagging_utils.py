# utils/tagging_utils.py
# This module provides utility functions for processing tags for summarized articles.
# It includes functions to parse JSON responses, insert tags into the database,
# update the status of articles, load system prompts, construct system prompts, and fetch articles.

import json
from datetime import datetime, timezone
from utils.db_utils import get_supabase_client, fetch_table_data
from utils.logging_utils import log_status, log_duration
from utils.llm_utils import call_llm_api
from config.config_loader import load_config
from task_management.celery_app import app

config = load_config()
table_names = config.get('tables', {})

def process_tags(article_id, response_content, status_entries):
    """
    Process the tags generated by the LLM and update the database.
    
    Args:
        article_id (int): The ID of the article being tagged.
        response_content (dict): The parsed response content from the LLM 
                                 containing tags and scores.
        status_entries (list): A list to store status messages for each tag insertion.
    
    Returns:
        dict: A dictionary containing a success or error message.
    """
    supabase = get_supabase_client()
    
    try:
        # Parse the JSON response (already done in call_llm_api)
        response_json = response_content 
        
        # Parse the JSON response
        response_json = json.loads(response_content)

        # Track statuses for each tag insertion
        successful_insertions = []

        # Flag to track if at least one tag was inserted successfully
        at_least_one_tag_inserted = False 

        for tag_data in response_json["tags"]:
            tag = tag_data["tag"]
            score = int(tag_data["score"])  # Convert the score to an integer
            try:
                # Insert the tag and score into the article_tags table
                supabase.table(table_names['article_tags']).insert({
                    "article_id": article_id,
                    "tag": tag,
                    "score": score
                }).execute()
                successful_insertions.append({"tag": tag, "status": "success"})
                at_least_one_tag_inserted = True  # Set the flag to True if insertion succeeds
            except Exception as insert_error:
                if "duplicate key value violates unique constraint" in str(insert_error):
                    # Log the rejected tag, but don't raise an exception
                    status_entries.append({"tag": tag, "status": "rejected", "error": str(insert_error)})
                else:
                    # Handle other errors - for now, we'll re-raise
                    status_entries.append({"tag": tag, "status": "failed", "error": str(insert_error)})
                    raise Exception(f"Failed to insert tag {tag} for article {article_id}: {insert_error}")

        # Only update ProductionReady status if at least one tag was successfully inserted
        if at_least_one_tag_inserted:
            supabase.table(table_names['summarizer_flow']).update({"ProductionReady": True}).eq("id", article_id).execute()

        return {"message": f"Tags generated and updated successfully for ID {article_id}"}

    except Exception as e:
        return {"message": f"Error during tag generation for ID {article_id}", "error": str(e)}

def construct_system_prompt():
    """
    Load system prompts from the configuration file and construct the system prompt.
    
    Returns:
        str: The constructed system prompt.
    """
    # Load system prompts from the configuration file
    config = load_config()
    system_prompt_tagger_1 = config['systemPrompt-Tagger-1']
    system_prompt_tagger_2 = config['systemPrompt-Tagger-2']

    # Fetch tags and construct the system prompt
    tags = fetch_table_data("all_tags", filters={"isEnabled": True}, columns=["tag", "public_desc", "private_desc"])
    list_of_tags_and_desc = '\n'.join([f"{tag['tag']} (Public: {tag['public_desc']}, Private: {tag['private_desc']})" for tag in tags])
    list_of_tags = ', '.join([tag['tag'] for tag in tags])
    system_prompt = f"{system_prompt_tagger_1} {list_of_tags_and_desc} {system_prompt_tagger_2} {list_of_tags}"
    
    return system_prompt

def fetch_articles():
    """
    Fetch articles that are summarized but not marked as production-ready from the summarizer_flow table.
    
    Returns:
        list: A list of articles matching the criteria.
    """
    return fetch_table_data(
        "summarizer_flow", 
        filters={"summarized": True}, 
        complex_filters="ProductionReady.is.false", 
        columns=["id", "ArticleTitle", "IntroParagraph", "BulletPointSummary", "ConcludingParagraph"]
    )

# Main function to process articles: fetches articles, calls LLM API to generate tags, and updates the database.
def process_articles(script_name, primary=True, api_call_func=None):
    # Record the start time for the process
    start_time = datetime.now(timezone.utc)
    # Initialize lists to store status entries, total items processed, and failed items
    status_entries = []
    total_items = 0
    failed_items = 0

    # Construct the system prompt using predefined tags and descriptions
    system_prompt = construct_system_prompt()
    # Fetch articles that need to be processed
    articles = fetch_articles()

    if articles:
        for article in articles:
            total_items += 1
            article_id = article["id"]
            content = f"{article['ArticleTitle']} {article['IntroParagraph']} {article['BulletPointSummary']} {article['ConcludingParagraph']}"
            # Call the LLM API to generate tags for the article
            result = api_call_func(content, system_prompt)
            # Process the generated tags and update the database
            process_result = process_tags(article_id, result, status_entries)
            # Check if the processing was successful and update the failed items count accordingly
            if not process_result.get("message").startswith("Tags generated and updated successfully"):
                failed_items += 1
    else:
        status_entries.append({"message": "No articles to tag"})

    # Log the status and duration of the process based on the number of failed items
    if failed_items == 0:
        log_status(script_name, status_entries, "Success")
        task_status = "Success"
    elif failed_items > 0 and failed_items < total_items:
        log_status(script_name, status_entries, "Partial")
        task_status = "Partial"
    else:
        log_status(script_name, status_entries, "Error")
        task_status = "Error"

    log_duration(script_name, start_time, datetime.now(timezone.utc))

    return "Success" if failed_items == 0 else "Partial" if failed_items > 0 and failed_items < total_items else "Error"
