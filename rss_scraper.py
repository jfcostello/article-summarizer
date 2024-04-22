#!/root/.ssh/article-summarizer/as-env/bin/python3

import feedparser
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Supabase setup using environment variables
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

def fetch_and_store_urls():
    # Fetch enabled RSS feed URLs from the rss_feed_list table
    rss_feeds_response = supabase.table("rss_feed_list").select("rss_feed").eq("isEnabled", 'TRUE').execute()

    # Check for errors in the response
    if not rss_feeds_response.data:
        print(f"Error fetching RSS feed URLs or no data found.")
        return

    rss_feeds_data = rss_feeds_response.data

    # Process each feed URL
    for feed in rss_feeds_data:
        feed_url = feed['rss_feed']
        newsfeed = feedparser.parse(feed_url)
        existing_urls_response = supabase.table("summarizer_flow").select("url").execute()
        
        if existing_urls_response.data is None:
            print(f"Failed to fetch existing URLs for {feed_url}.")
            continue

        existing_urls = {item['url'] for item in existing_urls_response.data}

        new_urls = [{'url': entry.get('link'), 'scraped': False} for entry in newsfeed.entries if entry.get('link') and entry.get('link') not in existing_urls]

        if new_urls:
            insert_response = supabase.table("summarizer_flow").insert(new_urls).execute()
            if insert_response.data is None:
                print(f"Failed to insert data for {feed_url}.")
            else:
                print(f"Data inserted successfully for {feed_url}")
        else:
            print(f"No new URLs to add for {feed_url}")

if __name__ == "__main__":
    fetch_and_store_urls()

