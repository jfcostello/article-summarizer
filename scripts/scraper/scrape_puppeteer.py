# scripts/scraper/scrape_puppeteer.py
# This script uses Pyppeteer to scrape article content from URLs stored in a Supabase database,
# with added logging and error handling to help diagnose URL-specific issues.
import sys
import os
import asyncio
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interfaces.scraper import Scraper
from utils.scraping_util import run_puppeteer_scraper
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
        logger = logging.getLogger("PuppeteerScraper")
        logger.info(f"Starting scrape for URL: {url}")
        browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.newPage()
        try:
            logger.info(f"Navigating to URL: {url}")
            await page.goto(url, {'waitUntil': 'domcontentloaded', 'timeout': 10000})
            logger.info(f"Page loaded for URL: {url}")
        except Exception as e:
            logger.error(f"Error navigating to URL {url}: {e}")
            await browser.close()
            raise e
        try:
            content = await page.evaluate('''() => document.body.innerText || "No content found"''')
            logger.info(f"Content scraped for URL: {url}")
        except Exception as e:
            logger.error(f"Error evaluating page content for URL {url}: {e}")
            await browser.close()
            raise e
        await browser.close()
        return content

    async def run(self):
        """
        Run the scraping process for all URLs that need to be scraped.
        """
        success = await run_puppeteer_scraper(self.scrape, script_name=os.path.basename(__file__))
        return success
    
if __name__ == "__main__":
    scraper = PuppeteerScraper()
    success = asyncio.run(scraper.run())
    sys.exit(0 if success else 1)
