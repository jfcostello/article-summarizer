import feedparser
from supabase import create_client, Client

# Supabase setup
url = "https://xcjslzaahazdvsqjxrap.supabase.co"  # Your Supabase project URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjanNsemFhaGF6ZHZzcWp4cmFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTMzODE3MjUsImV4cCI6MjAyODk1NzcyNX0.alOSOmX0x8-1j2hqNfoi7WlBVBWvexIZiuX3Y5THg_4"  # Your Supabase anon/public key
supabase: Client = create_client(url, key)

def fetch_and_store_urls():
    feed_url = "https://www.theverge.com/rss/index.xml"
    newsfeed = feedparser.parse(feed_url)
    urls = [{'url': entry.get('link'), 'scraped': False} for entry in newsfeed.entries if entry.get('link')]
    
    # Insert URLs into Supabase, with 'scraped' set to False by default
    data, error = supabase.table("rss_urls").insert(urls).execute()

    # Better handling for the benign 'error'
    if error and error != ('count', None):
        print(f"Failed to insert data: {error}")  # Log the error if it's not the benign ('count', None)
    else:
        print("Data inserted successfully", data)

if __name__ == "__main__":
    fetch_and_store_urls()