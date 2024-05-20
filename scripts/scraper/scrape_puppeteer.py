#!/root/.ssh/article-summarizer/as-env/bin/python3
# scripts/scraper/scrape_puppeteer.py
# This script uses Pyppeteer to scrape article content from URLs stored in a Supabase database,
# logs the scraping status and duration, and updates the database with the scraped content.

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interfaces.scraper import Scraper
from utils.scraping_util import run_puppeteer_scraper  # Import the new wrapper function
import asyncio
from pyppeteer import launch

class PuppeteerScraper(Scraper):
    """
    Scraper implementation using Pyppeteer to scrape content from URLs.
    """

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
        await run_puppeteer_scraper(self.scrape)

if __name__ == "__main__":
    scraper = PuppeteerScraper()
    asyncio.run(scraper.run())
