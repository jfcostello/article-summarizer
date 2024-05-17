#!/root/.ssh/article-summarizer/as-env/bin/python3
import os
import json
import yaml
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
script_name = "groq_llama_8b_tagger.py"

# Load YAML configuration for system prompt
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config['systemPrompt-Tagger-1'], config['systemPrompt-Tagger-2']

def fetch_tags():
    """Fetch enabled tags with descriptions from the all_tags table."""
    response = supabase.table("all_tags").select("tag, public_desc, private_desc").eq("isEnabled", True).execute()
    tags = response.data if response.data else []
    return tags

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
    """Fetch articles that are summarized but not production-ready."""
    response = (
        supabase.table("summarizer_flow")
        .select("id, ArticleTitle, IntroParagraph, BulletPointSummary, ConcludingParagraph")
        .eq("summarized", True)
        .is_("ProductionReady", False)
        .execute()
    )
    articles = response.data if response.data else []
    return articles

def generate_tags(article_id, content, systemPrompt):
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

        # Extract the JSON response
        response_content = chat_completion.choices[0].message.content
        response_json = json.loads(response_content)

        # Track statuses for each tag insertion
        status_entries = []
        successful_insertions = []

        for tag_data in response_json["tags"]:
            tag = tag_data["tag"]
            score = int(tag_data["score"])  # Convert the score to an integer
            try:
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



def main():
    start_time = datetime.now(timezone.utc)
    articles = fetch_articles()
    status_entries = []
    systemPrompt_Tagger_1, systemPrompt_Tagger_2 = load_config()
    tags = fetch_tags()

    # Construct the listoftagsanddesc string
    listoftagsanddesc = '\n'.join([f"{tag['tag']} (Public: {tag['public_desc']}, Private: {tag['private_desc']})" for tag in tags])
    listoftags = ', '.join([tag['tag'] for tag in tags])  # Only the tags

    # Construct the system prompt with the descriptions and just the tags
    system_prompt = f"{systemPrompt_Tagger_1} {listoftagsanddesc} {systemPrompt_Tagger_2} {listoftags}"

    if articles:
        for article in articles:
            article_id = article["id"]
            content = article["ArticleTitle"] + " " + article["IntroParagraph"] + " " + article["BulletPointSummary"] + " " + article["ConcludingParagraph"]
            result = generate_tags(article_id, content, system_prompt)
            status_entries.append(result)
    else:
        print("No articles to tag.")
        status_entries.append({"message": "No articles to tag"})

    end_time = datetime.now(timezone.utc)
    log_duration(script_name, start_time, end_time)
    log_status(script_name, status_entries, "Complete")

if __name__ == "__main__":
    main()
