#!/root/.ssh/article-summarizer/as-env/bin/python3
import os
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

def fetch_articles():
    """Fetch articles that have been scraped but not summarized."""
    response = supabase.table("summarizer_flow").select("id, content").eq("scraped", True).eq("summarized", False).execute()
    articles = response.data if response.data else []
    return articles

def parse_structured_text(text):
    """Parse pipe-separated structured text into a dictionary, handling complex entries."""
    data = {}
    entries = text.strip('"').split('|')
    last_key = None  # Track the last key for entries that are part of a list
    for entry in entries:
        if ':' in entry:
            parts = entry.split(':', 1)
            if len(parts) == 2:
                key, value = parts
                key = key.strip()
                value = value.strip().replace('\n', ' ')  # Normalize newlines and trim spaces
                if "BulletPointSummary" in key:
                    data[key] = [bp.strip('- ').strip() for bp in value.split('. -') if bp.strip()]
                else:
                    data[key] = value
                last_key = key
            else:
                print(f"Warning: Unable to parse entry '{entry}'. Skipping this entry.")
        else:
            # If no key is found, append the entry to the last known key if possible
            if last_key and "BulletPointSummary" in last_key:
                data[last_key].append(entry.strip('- ').strip())
            else:
                print(f"Warning: Unable to append entry '{entry}' to any key. Skipping this entry.")

    return data

def summarize_article(article_id, content):
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=4000,
            temperature=0,
            messages=[
                {"role": "user", "content": content},
                {"role": "system", "content": '''You are an article summarizer. A headless browser will scrape the contents of an article, and your role is to turn it into a succinct bullet point based summary which will be delivered in pipe-separated values. Your response should only be in pipe separated values, as it will be ingested into a database directly. Do not include anything else. When creating the summary, make sure you focus only on the article itself. You will get the full page, but ignore any additional articles, comments etc. The article will be the bulk of the return, usually starting with a title and ending with comments, a heading promoting additional articles, a complete change in tone things of that nature - you should only focus on the article, so look out for signs the article ended, like a conclusion or a sudden change into comments, other articles, footers etc. Focus on only summarizing, do not add additional information or context - if it's not in the article, don't include it. Your summary should 1) Start with the title 2) Have a very brief intro explaining what the article is about 3) Have 2-6 bullet points explaining what is covered in the article. For smaller articles, use less bullet points, only use more if there truly are lots of things to discuss. If a person is quoted, and the quote is relevant, include the full quote in the return and attribute it to who it is attributed to in the article. 4) Close with A very brief outro summarizing the article. This will be returned in pipe-separated values as follows ---"ArticleTitle: TITLE OF ARTICLE GOES HERE|IntroParagraph: BRIEF INTRO THAT EXPLAINS WHAT THE ARTICLE IS ABOUT GOES HERE|BulletPointSummary: - BULLET POINT GOES HERE. - ADDITIONAL BULLET POINT GOES HERE - Players can opt to only see these emotes from friends, or hide them altogether. - CONTINUE WITH BULLET POINTS AS NECESSARY, ENDING WITH 2-6 DEPENDING ON HOW MANY DISTINCT TOPICS ARE DISCUSSED IN THE ARTICLE|ConcludingParagraph: BRIEF CONCLUDING PARAGRAPH GOES HERE". Remember, do not include any additional content, the first character in your response should be "'''}
            ]
        )

        # Extract the structured text from the response
        response_content = chat_completion.choices[0].message.content
        summary_data = parse_structured_text(response_content)

        update_data = {
            "ArticleTitle": summary_data.get("ArticleTitle", "N/A"),
            "IntroParagraph": summary_data.get("IntroParagraph", "N/A"),
            "BulletPointSummary": json.dumps(summary_data.get("BulletPointSummary", [])),  # Default to empty list if not found
            "ConcludingParagraph": summary_data.get("ConcludingParagraph", "N/A"),
            "summarized": True  # Set summarized to True once the article has been successfully summarized
        }

        update_response, update_error = supabase.table("summarizer_flow").update(update_data).eq("id", article_id).execute()

        if update_error and update_error != ('count', None):
            print(f"Failed to update summary for ID {article_id}: {update_error}")
        else:
            print(f"Summary updated successfully for ID {article_id}")
    except Exception as e:
        print(f"Error during the summarization process for ID {article_id}: {str(e)}")

def main():
    articles = fetch_articles()
    if articles:
        for article in articles:
            summarize_article(article['id'], article['content'])
    else:
        print("No articles to summarize.")

if __name__ == "__main__":
    main()