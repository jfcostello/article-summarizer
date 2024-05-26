import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery, chain
from celery.schedules import crontab
from config.config_loader import load_config
import subprocess

config = load_config()

app = Celery('tasks', broker=config['celery']['broker_url'])
app.conf.update(
    result_backend=config['celery']['result_backend'],
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'fetch-urls-every-2-minutes': {
            'task': 'task_management.celery_app.fetch_urls',
            'schedule': crontab(minute='*/2'),
        },
        'execute-additional-tasks-every-30-minutes': {
            'task': 'task_management.celery_app.execute_additional_tasks',
            'schedule': crontab(minute='*/30'),
        },
    }
)

@app.task(name='task_management.celery_app.fetch_urls')
def fetch_urls():
    result = subprocess.run([sys.executable, "scripts/main.py", "fetch_urls", "true"], capture_output=True, text=True)
    if result.returncode == 0:
        try:
            total_new_urls = int(result.stdout.strip())
            return total_new_urls
        except ValueError:
            return 0
    return 0

@app.task(name='task_management.celery_app.scraper')
def scraper():
    subprocess.run([sys.executable, "scripts/main.py", "scrape_content", "true"], check=True)

@app.task(name='task_management.celery_app.summarizer')
def summarizer():
    subprocess.run([sys.executable, "scripts/main.py", "summarize_articles", "true"], check=True)

@app.task(name='task_management.celery_app.tagging')
def tagging():
    subprocess.run([sys.executable, "scripts/main.py", "tag_articles", "true"], check=True)

@app.task(name='task_management.celery_app.execute_additional_tasks')
def execute_additional_tasks():
    task_chain = chain(
        scraper.s(),
        summarizer.s(),
        tagging.s()
    )
    task_chain()

@app.task(name='task_management.celery_app.update_status')
def update_status(task_name, task_statuses, task_status):
    # Your code to update status
    pass
