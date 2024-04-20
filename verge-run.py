import subprocess

def run_script(command):
    """ Utility function to run a shell command. """
    try:
        subprocess.run(command, check=True)
        print(f"Successfully ran: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run: {' '.join(command)} with error: {e}")

def main():
    # Part 1: Run the RSS scraper script
    run_script(['python3', 'verge-rss_scraper.py'])

    # Part 2: Run the Puppeteer script to scrape articles
    # Assuming you have Node.js and Puppeteer set up
    run_script(['node', 'verge-extract-article-puppeteer.js'])

    # Part 3: Run the Claude AI summarization script
    run_script(['python3', 'verge-claude.py'])

if __name__ == "__main__":
    main()