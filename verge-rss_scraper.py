import feedparser
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Supabase setup using environment variables
url = os.getenv('SUPABASE_URL')  # Use the environment variable
key = os.getenv('SUPABASE_KEY')  # Use the environment variable
supabase: Client = create_client(url, key)

def fetch_and_store_urls():
    feed_url = "https://www.theverge.com/rss/index.xml"
    newsfeed = feedparser.parse(feed_url)
    
    # Fetch existing URLs from the database
    existing_urls_response = supabase.table("rss_urls").select("url").execute()
    existing_urls = {item['url'] for item in existing_urls_response.data} if existing_urls_response.data else set()

    # Filter out URLs that are already in the database
    new_urls = [{'url': entry.get('link'), 'scraped': False} for entry in newsfeed.entries if entry.get('link') and entry.get('link') not in existing_urls]
    
    if new_urls:
        data, error = supabase.table("rss_urls").insert(new_urls).execute()
        if error and error != ('count', None):
            print(f"Failed to insert data: {error}")  # Log the error if it's not the benign ('count', None)
        else:
            print("Data inserted successfully", data)
    else:
        print("No new URLs to add.")

if __name__ == "__main__":
    fetch_and_store_urls()