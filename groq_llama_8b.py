#!/root/.ssh/article-summarizer/as-env/bin/python3
import os
import json
import yaml
import re
from datetime import datetime, timezone
from supabase import create_client, Client
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase setup using environment variables
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_KEY')
)

# Groqs client setup using environment variable
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Define script_name globally
script_name = "groq_llama_8b.py"

# Load YAML configuration for system prompt
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config['systemPrompt']

def custom_escape_quotes(json_str):
    # Correctly escape quotes inside JSON string values, avoiding double escaping
    json_str = re.sub(r'(?<=: )"(.+?)"(?=,|\s*\})', lambda m: '"' + m.group(1).replace('"', '\\"') + '"', json_str)
    return json_str

def log_status(script_name, log_entries, status):
    """Logs script execution status and messages."""
    supabase.table("log_script_status").insert({
        "script_name": script_name,
        "log_entry": json.dumps(log_entries),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status
    }).execute()


def log_duration(script_name, start_time, end_time):
    """Logs script execution duration."""
    duration_seconds = (end_time - start_time).total_seconds()
    supabase.table("log_script_duration").insert({
        "script_name": script_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds
    }).execute()

def fetch_articles():
    """Fetch articles that have been scraped but not summarized."""
    response = supabase.table("summarizer_flow").select("id, content").eq("scraped", True).eq("summarized", False).execute()
    articles = response.data if response.data else []
    return articles

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

def summarize_article(article_id, content, status_entries, systemPrompt):
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=4000,
            temperature=0,
            messages=[
                {"role": "user", "content": content},
                {"role": "system", "content": systemPrompt}
            ]
        )

        # Extract the structured text from the response
        response_content = chat_completion.choices[0].message.content
        ## print("Debug - Response Content:", response_content)  # Debugging output
        intro_paragraph = extract_section(response_content, "IntroParagraph:", "BulletPointSummary:")
        bullet_point_summary = extract_section(response_content, "BulletPointSummary:", "ConcludingParagraph:")
        bullet_point_summary = custom_escape_quotes(bullet_point_summary)
        concluding_paragraph = extract_section(response_content, "ConcludingParagraph:")

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

def main():
    start_time = datetime.now(timezone.utc)
    articles = fetch_articles()
    status_entries = []
    system_prompt = load_config()
    if articles:
        for article in articles:
            summarize_article(article['id'], article['content'], status_entries, system_prompt)
    else:
        print("No articles to summarize.")
        status_entries.append({"message": "No articles to summarize"})

    end_time = datetime.now(timezone.utc)
    log_duration(script_name, start_time, end_time)
    log_status(script_name, status_entries, "Complete")

if __name__ == "__main__":
    main()