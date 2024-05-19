# scripts/scraper/scrape_puppeteer.py
# This script uses Pyppeteer to scrape article content from URLs stored in a Supabase database,
# logs the scraping status and duration, and updates the database with the scraped content.

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interfaces.scraper import Scraper
from utils.db_utils import get_supabase_client, fetch_table_data, update_table_data
from utils.logging_utils import log_status, log_duration
import asyncio
from datetime import datetime
from pyppeteer import launch

class PuppeteerScraper(Scraper):
    """
    Scraper implementation using Pyppeteer to scrape content from URLs.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def scrape(self, url):
        """
        Scrape content from the given URL using Pyppeteer.
        
        Args:
            url (str): The URL to scrape content from.
        
        Returns:
            str: The scraped content.
        """
        browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.newPage()
        await page.goto(url, {'waitUntil': 'domcontentloaded', 'timeout': 10000})
        content = await page.evaluate('''() => document.body.innerText || "No content found"''')
        await browser.close()
        return content

    async def run(self):
        """
        Run the scraping process for all URLs that need to be scraped.
        """
        start_time = datetime.now()
        log_entries = []

        urls_to_scrape = fetch_table_data('summarizer_flow', {'scraped': False})

        if not urls_to_scrape:
            log_entries.append({"message": "No URLs to process."})
            log_status('scrape_puppeteer.py', log_entries, 'No URLs')
            log_duration('scrape_puppeteer.py', start_time, datetime.now())
            return

        for record in urls_to_scrape:
            url = record['url']
            try:
                content = await self.scrape(url)
                update_data = {'content': content, 'scraped': True}
                update_table_data('summarizer_flow', update_data, ('id', record['id']))
                log_entries.append({"message": f"Content updated successfully for URL {url}"})
            except Exception as e:
                log_entries.append({"message": f"Failed to scrape {url}: {str(e)}", "error": str(e)})

        end_time = datetime.now()
        log_status('scrape_puppeteer.py', log_entries, 'Complete')
        log_duration('scrape_puppeteer.py', start_time, end_time)

if __name__ == "__main__":
    scraper = PuppeteerScraper()
    asyncio.run(scraper.run())
