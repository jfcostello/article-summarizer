from celery import shared_task, chain
import subprocess
from task_management.celery_app import app

@shared_task
def fetch_urls_task():
    result = subprocess.run(["python", "scripts/main.py", "fetch_urls", "true"], capture_output=True, text=True)
    if result.returncode == 0:
        try:
            total_new_urls = int(result.stdout.strip())
            return total_new_urls
        except ValueError:
            return 0
    return 0

@shared_task
def scrape_content_task():
    subprocess.run(["python", "scripts/main.py", "scrape_content", "true"], check=True)

@shared_task
def summarize_articles_task():
    subprocess.run(["python", "scripts/main.py", "summarize_articles", "true"], check=True)

@shared_task
def tag_articles_task():
    subprocess.run(["python", "scripts/main.py", "tag_articles", "true"], check=True)

@app.task
def run_dependent_tasks(total_new_urls):
    if total_new_urls > 0:
        task_chain = chain(
            scrape_content_task.s(),
            summarize_articles_task.s(),
            tag_articles_task.s()
        )
        task_chain()

@shared_task
def execute_additional_tasks():
    task_chain = chain(
        scrape_content_task.s(),
        summarize_articles_task.s(),
        tag_articles_task.s()
    )
    task_chain()

