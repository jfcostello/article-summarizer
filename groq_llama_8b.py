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

def summarize_article(article_id, content):
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=4000,
            temperature=0,
            messages=[
                {"role": "user", "content": content},
                {"role": "system", "content": 'You are an article summarizer. A headless browser will scrape the contents of an article, and your role is to turn it into a succinct bullet point based summary which will be delivered in json. Your response should only be in JSON, as it will be ingested into a database directly. When creating the summary, make sure you focus only on the article itself. You will get the full page, but ignore any additional articles, comments etc. The article will be the bulk of the return, usually starting with a title and ending with comments, a heading promoting additional articles, a complete change in tone things of that nature - you should only focus on the article, so look out for signs the article ended, like a conclusion or a sudden change into comments, other articles, footers etc. Focus on only summarizing, do not add additional information or context - if it\'s not in the article, don\'t include it. Your summary should 1) Start with the title 2) Have a very brief intro explaining what the article is about 3) Have 2-6 bullet points explaining what is covered in the article. For smaller articles, use less bullet points, only use more if there truly are lots of things to discuss. If a person is quoted, and the quote is relevant, include the full quote in the return and attribute it to who it is attributed to in the article. 4) Close with A very brief outro summarizing the article. This will be returned in JSON as follows: {"ArticleTitle":"TITLE OF ARTICLE GOES HERE", "IntroParagraph":"BRIEF INTRO THAT EXPLAINS WHAT THE ARTICLE IS ABOUT GOES HERE", "BulletPointSummary":["BULLET POINT GOES HERE", "ADDITIONAL BULLET POINT GOES HERE", "CONTINUE WITH BULLET POINTS AS NECESSARY, ENDING WITH 2-6 DEPENDING ON HOW MANY DISTINCT TOPICS ARE DISCUSSED IN THE ARTICLE"], "ConcludingParagraph":"BRIEF CONCLUDING PARAGRAPH GOES HERE"}'}
            ]
        )

        # Accessing the correct summary text from the chat completion response
        summary_text = chat_completion.choices[0].message.content  # Corrected line to access text

        # Update the database with the summary and set 'summarized' to True
        update_data, update_error = supabase.table("summarizer_flow").update({"summary": summary_text, "summarized": True}).eq("id", article_id).execute()

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