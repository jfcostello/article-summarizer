from celery import shared_task
import subprocess
from task_management.celery_app import app

@shared_task
def fetch_urls_task():
    result = subprocess.run(["python", "scripts/main.py", "fetch_urls"], capture_output=True, text=True)
    if result.returncode == 0:
        total_new_urls = int(result.stdout.strip())
        if total_new_urls > 0:
            run_dependent_tasks.delay()

@app.task
def run_dependent_tasks():
    subprocess.run(["python", "scripts/main.py", "scrape_content"], check=True)
    subprocess.run(["python", "scripts/main.py", "summarize_articles"], check=True)
    subprocess.run(["python", "scripts/main.py", "tag_articles"], check=True)

@app.task
def scrape_content():
    subprocess.run(["python", "scripts/main.py", "scrape_content"], check=True)

@app.task
def summarize_articles():
    subprocess.run(["python", "scripts/main.py", "summarize_articles"], check=True)

@app.task
def tag_articles():
    subprocess.run(["python", "scripts/main.py", "tag_articles"], check=True)
