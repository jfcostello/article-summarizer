import os
from supabase import create_client, Client
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase setup using environment variables
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_KEY')
)

# Anthropics client setup using environment variable
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

def fetch_articles():
    """Fetch articles that have been scraped but not summarized."""
    response = supabase.table("rss_urls").select("id, content").eq("scraped", True).eq("summarized", False).execute()
    articles = response.data if response.data else []
    return articles

def summarize_article(article_id, content):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            system = ('You are an article summarizer. A headless browser will scrape the contents of an article, and your role is to turn it into a succinct, bullet point based read. It is from the verge. They include extra content, unrelated to the article, which should be ignored. The end of the article is marked by the content "NEW FEATURED VIDEOS FROM THE VERGE" - disregard everything after that, that text showing up signifies the end of the article and the end of the content you should consider. Make sure your summary is strictly a summary of the article, never include additional information - always just return the article. So if you have additional information, eg you know when something in an article was implemented, or you know more about something briefly mentioned, do not include that in your return. Just focus on the content supplied to you. Your summary should 1) Start with the title 2) Have a very brief intro explaining what the article is about 3) Have 2-6 bullet points explaining what is covered in the article. For smaller articles, use less bullet points, only use more if there truly are lots of things to discuss. If a person is quoted, and the quote is relevant, include the full quote in the return and attribute it to who it is attributed to in the article. 4) Close with A very brief outro summarizing the article 5) Finally include the URL of the article'),
            temperature=0,
            messages=[{"role": "user", "content": content}]
    )

        # Assuming the response content is already a plain text or handling it as such
        summary_text = response.content.text if hasattr(response.content, 'text') else str(response.content)

        # Update the database with the summary and set 'summarized' to True
        update_data, update_error = supabase.table("rss_urls").update({"summary": summary_text, "summarized": True}).eq("id", article_id).execute()
        
        # Handle 'count' response which is not an actual error
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