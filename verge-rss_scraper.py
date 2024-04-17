import feedparser

# Define the URL of the RSS feed
url = "https://www.theverge.com/rss/index.xml"

# Parse the feed
newsfeed = feedparser.parse(url)

# List to store URLs
urls = []

# Iterate over each entry in the feed
for entry in newsfeed.entries:
    article_link = entry.get('link')
    if article_link:
        urls.append(article_link)

# Optionally, write URLs to a file
with open('verge-urls.txt', 'w') as f:
    for url in urls:
        f.write(url + '\n')