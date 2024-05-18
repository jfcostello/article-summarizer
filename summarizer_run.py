#!/root/.ssh/article-summarizer/as-env/bin/python3
#This script, summarizer_run.py, orchestrates the execution of various scripts related to article summarization, logging their statuses and durations into a Supabase database. It utilizes environment variables for configuration, runs a set of predefined scripts, and logs both the execution results and the time taken for each script.
# It's on a cron job to run every 30 minutes on my server, it executes the full run from fetching urls from the RSS feed, to scraping the articles of those URLs, to summarizing those articles, to tagging and scoring the articles
import subprocess
import sys
import os
import json
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase setup using environment variables
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

# Logs script execution status and messages to the Supabase database.
def log_status(script_name, log_entries, status):
    """Logs script execution status and messages."""
    supabase.table("log_script_status").insert({
        "script_name": script_name,
        "log_entry": json.dumps({"messages": log_entries}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status
    }).execute()

# Logs the start and end times, as well as the duration of script execution, to the Supabase database.
def log_duration(script_name, start_time, end_time):
    """Logs script execution duration."""
    duration_seconds = (end_time - start_time).total_seconds()
    supabase.table("log_script_duration").insert({
        "script_name": script_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds
    }).execute()

# Utility function to run a shell or Node.js command, capturing and logging the results.
def run_script(command):
    """ Utility function to run a shell or Node.js command. """
    if isinstance(command, str):  # Check if the command is a string
        # Determine Python command based on OS
        python_command = 'python3' if sys.platform != 'win32' else 'python'
        command = [python_command] + command.split()  # Split the command string into list
    log_entries = []
    try:
        subprocess.run(command, check=True)
        log_entries.append(f"Successfully ran: {' '.join(command)}")
        return "Success", log_entries
    except subprocess.CalledProcessError as e:
        log_entries.append(f"Failed to run: {' '.join(command)} with error: {e}")
        return "Error", log_entries

# Main function that executes a series of scripts, logging their status and execution duration.
def main():
    # Capture the start time of the script execution
    start_time = datetime.now(timezone.utc)
    # Initialize log entries and overall status
    all_log_entries = []

    # Run the scripts one by one, capturing logs and continuing even if one fails
    # Iterate over and run each script, capturing their logs
    # This sets the order the scripts will run in for the full summarizer run
    for script in ['rss_scraper.py', ['node', 'extract_article_puppeteer.js'],
                   'groq_llama_8b.py', 'claude.py', 'groq_llama_8b_tagger.py']:
        # Update log entries and overall status based on script execution results
        status, log_entries = run_script(script)
        all_log_entries.extend(log_entries)
        if status == "Error":
            overall_status = "Error"


    # Capture the end time of the script execution
    end_time = datetime.now(timezone.utc)
    # Log the final status and execution duration
    log_status("summarizer_run.py", all_log_entries, status)
    log_duration("summarizer_run.py", start_time, end_time)

# Entry point for the script
if __name__ == "__main__":
    main()
