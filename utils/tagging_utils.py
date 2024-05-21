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

def process_tags(article_id, chat_completion, status_entries):
    """
    Process the tags generated by the LLM and update the database.
    
    Args:
        article_id (int): The ID of the article being tagged.
        chat_completion (object): The response object from the LLM containing tags and scores.
        status_entries (list): A list to store status messages for each tag insertion.
    
    Returns:
        dict: A dictionary containing a success or error message.
    """
    supabase = get_supabase_client()
    
    try:
        # Extract the JSON response
        response_content = chat_completion.choices[0].message.content
        
        # Parse the JSON response
        response_json = json.loads(response_content)

        # Track statuses for each tag insertion
        successful_insertions = []

        for tag_data in response_json["tags"]:
            tag = tag_data["tag"]
            score = int(tag_data["score"])  # Convert the score to an integer
            try:
                # Insert the tag and score into the article_tags table
                supabase.table("article_tags").insert({
                    "article_id": article_id,
                    "tag": tag,
                    "score": score
                }).execute()
                successful_insertions.append({"tag": tag, "status": "success"})
            except Exception as insert_error:
                status_entries.append({"tag": tag, "status": "failed", "error": str(insert_error)})
                raise Exception(f"Failed to insert tag {tag} for article {article_id}: {insert_error}")

        # Only update ProductionReady status if all tags were successfully inserted
        if all(entry["status"] == "success" for entry in successful_insertions):
            supabase.table("summarizer_flow").update({"ProductionReady": True}).eq("id", article_id).execute()

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

def process_articles(script_name, primary=True, api_call_func=None):
    """
    Process articles by fetching them, generating tags, and logging the process and duration.
    
    Args:
        script_name (str): The name of the script for logging purposes.
        primary (bool, optional): Whether to use primary logic. Defaults to True.
        api_call_func (function, optional): The function to call the specific LLM API. Defaults to None.
    """
    start_time = datetime.now(timezone.utc)
    status_entries = []

    # Construct the system prompt
    system_prompt = construct_system_prompt()

    # Fetch articles
    articles = fetch_articles()

    # Process articles
    if articles:
        for article in articles:
            article_id = article["id"]
            content = f"{article['ArticleTitle']} {article['IntroParagraph']} {article['BulletPointSummary']} {article['ConcludingParagraph']}"
            result = api_call_func(content, system_prompt)
            process_result = process_tags(article_id, result, status_entries)
            status_entries.append(process_result)
    else:
        status_entries.append({"message": "No articles to tag"})

    end_time = datetime.now(timezone.utc)
    log_duration(script_name, start_time, end_time)
    log_status(script_name, status_entries, "Complete")
