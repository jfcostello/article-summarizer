# This script automates the summarization of scraped articles by interacting with the Anthropics API to generate summaries and then storing the results in a Supabase database. It includes functions for logging script status and duration, fetching articles needing summaries, extracting text sections from content, and processing each article through the summarization API. The configuration and API keys are loaded from environment variables.
# This is a backup script. It currently runs after the Groq script, it's job is to clean up anything the Groq scriped failed to do, usually because of rate limitations
# Unlike the Groq script,iIt also grabs articles where summarized is marked as true but introparagrpah, bulletpointsummary or concludingparagraph are empty. If Groq script fails to update one of those, usually bulletpointsummary due to bad json, it'll still mark the row as summarized to prevent an infinite loop where it keeps trying and failing to update. This script will then come in and finish the summarization
#!/root/.ssh/article-summarizer/as-env/bin/python3
import os
import json
import yaml
import re
from datetime import datetime, timezone
from supabase import create_client, Client
import anthropic
from dotenv import load_dotenv

# Load environment variables from the .env file to configure the script
load_dotenv()

# Initialize Supabase client using the URL and API key from environment variables
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_KEY')
)

# Initialize Anthropics client using the API key from environment variables
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

# Define the global script name for logging purposes
script_name = "claude.py"

# Load the system prompt configuration from config.yaml
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config['systemPrompt']

# Inserts escape characters into JSON strings to avoid double escaping we cannot correct on frontend, using RegEx
def custom_escape_quotes(json_str):
    # Correctly escape quotes inside JSON string values, avoiding double escaping
    json_str = re.sub(r'(?<=: )"(.+?)"(?=,|\s*\})', lambda m: '"' + m.group(1).replace('"', '\\"') + '"', json_str)
    return json_str

# Log the execution status and messages to the Supabase database
def log_status(script_name, log_entries, status):
    """Logs script execution status and messages."""
    try:
        response = supabase.table("log_script_status").insert({
            "script_name": script_name,
            "log_entry": json.dumps(log_entries),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status
        }).execute()
        # Check if 'error' is an attribute of the response and print if it is present
        if hasattr(response, 'error') and response.error:
            print("Failed to log status:", response.error.message)
    except Exception as e:
        print("Exception when logging status:", str(e))

# Log the script execution duration to the Supabase database
def log_duration(script_name, start_time, end_time):
    """Logs script execution duration."""
    duration_seconds = (end_time - start_time).total_seconds()
    try:
        response = supabase.table("log_script_duration").insert({
            "script_name": script_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds
        }).execute()
        # Check if 'error' is an attribute of the response and print if it is present
        if hasattr(response, 'error') and response.error:
            print("Failed to log duration:", response.error.message)
    except Exception as e:
        print("Exception when logging duration:", str(e))

# Fetch articles that are scraped but not fully summarized or have empty sections
# Unlike Groq, is fetching not just on summarized=false, but also if ANY of IntroPagraph, BulletPointSummary or ConcludingParagraph are empty
def fetch_articles():
    """Fetch articles that have been scraped but not fully summarized or have empty sections."""
    query = supabase.table("summarizer_flow").select("id, content")\
        .eq("scraped", True)\
        .or_("summarized.eq.false,IntroParagraph.is.null,IntroParagraph.eq.,BulletPointSummary.is.null,BulletPointSummary.eq.,ConcludingParagraph.is.null,ConcludingParagraph.eq.")
    response = query.execute()
    articles = response.data if response.data else []
    return articles

# Extract text between start_key and optional end_key from content, this breaks the response into the different columns we need using the exact text
def extract_section(content, start_key, end_key=None):
    """Extract text between start_key and optional end_key from content."""
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

# Use Claude to summarize the  of an article and update the Supabase database with the result
def summarize_article(article_id, content, status_entries, systemPrompt):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            system=(systemPrompt),
            temperature=0,
            messages=[{"role": "user", "content": content}]
    )

        if response.content and isinstance(response.content, list):
            structured_text = getattr(response.content[0], 'text', None)
            if structured_text:
                ## print("Debug - Structured Text:", structured_text)  # Debugging output to log the received text
                intro_paragraph = extract_section(structured_text, "IntroParagraph:", "BulletPointSummary:")
                bullet_point_summary = extract_section(structured_text, "BulletPointSummary:", "ConcludingParagraph:")
                bullet_point_summary = custom_escape_quotes(bullet_point_summary)
                concluding_paragraph = extract_section(structured_text, "ConcludingParagraph:")
            else:
                raise ValueError("Text attribute not found in response")
        else:
            raise ValueError("Invalid response format or empty content")

        update_data = {
            "IntroParagraph": intro_paragraph,
            "BulletPointSummary": bullet_point_summary,
            "ConcludingParagraph": concluding_paragraph,
            "summarized": True
        }

        update_response, update_error = supabase.table("summarizer_flow").update(update_data).eq("id", article_id).execute()
        if update_error and update_error != ('count', None):
            print(f"Failed to update summary for ID {article_id}: {update_error}")
            status_entries.append({"message": f"Failed to update summary for ID {article_id}", "error": str(update_error)})
        else:
            print(f"Summary updated successfully for ID {article_id}")
            status_entries.append({"message": f"Summary updated successfully for ID {article_id}"})

    except Exception as e:
        print(f"Error during the summarization process for ID {article_id}: {str(e)}")
        status_entries.append({"message": f"Error during summarization for ID {article_id}", "error": str(e)})

# Main function to execute the script workflow
def main():
    start_time = datetime.now(timezone.utc)  # Start time of the script
    articles = fetch_articles()
    status_entries = []
    system_prompt = load_config()
    if articles:
        for article in articles:
            summarize_article(article['id'], article['content'], status_entries, system_prompt)
    else:
        print("No articles to summarize.")
        status_entries.append({"message": "No articles to summarize"})

    end_time = datetime.now(timezone.utc)  # End time of the script
    log_duration(script_name, start_time, end_time)  # Log total duration once
    log_status(script_name, status_entries, "Complete")

# Entry point of the script
if __name__ == "__main__":
    main()