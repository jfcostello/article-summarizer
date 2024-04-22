#!/root/.ssh/article-summarizer/as-env/bin/python3
import subprocess
import sys

# Allows me to run this on both windows, expecting 'python', and Linux server, expecting 'python3'
def run_script(command):
    """ Utility function to run a shell or Node.js command. """
    if isinstance(command, str):  # Check if the command is a string
        # Determine Python command based on OS
        python_command = 'python3' if sys.platform != 'win32' else 'python'
        command = [python_command] + command.split()  # Split the command string into list

    try:
        subprocess.run(command, check=True)
        print(f"Successfully ran: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run: {' '.join(command)} with error: {e}")

def main():
    # Part 1: Run the RSS scraper script
    run_script('rss_scraper.py')

    # Part 2: Run the Puppeteer script to scrape articles
    run_script(['node', 'extract_article_puppeteer.js'])

    # Part 3: Run the Groq summarization script
    run_script('groq_llama_8b.py')

    # Part 4: Run the Claude AI summarization script as a backup to clean up anything not done by Groq due to time out or other issues, if Groq ran without issue this will not do anything
    run_script('claude.py')

if __name__ == "__main__":
    main()