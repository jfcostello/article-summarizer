import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery, chain
from celery.schedules import crontab
from config.config_loader import load_config
import subprocess
from datetime import datetime, timedelta
from scripts.redundancy_manager import execute_script
from utils.url_fetch_utils import process_feeds
from scripts.fetch_urls.fetch_urls_feedparser import FeedparserFetcher

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
        'check-execute-additional-tasks-every-30-minutes': {
            'task': 'task_management.celery_app.check_execute_additional_tasks',
            'schedule': crontab(minute='*/30'),
        },
        'process-task-queue-every-minute': {
            'task': 'task_management.celery_app.process_task_queue',
            'schedule': crontab(minute='*/1'),
        },
    }
)

task_queue = []

@app.task(name='task_management.celery_app.fetch_urls')
def fetch_urls():
    feedparser_fetcher = FeedparserFetcher()
    total_new_urls = process_feeds(parse_feed=feedparser_fetcher.parse_feed, app=app)
    if total_new_urls > 0:
        task_queue.append('execute_additional_tasks')
    return total_new_urls

@app.task(bind=True, name='task_management.celery_app.scraper', time_limit=420, soft_time_limit=300)
def scraper(self):
    try:
        status = execute_script("scripts/scraper/scrape_puppeteer.py")
        return status
    except Exception as exc:
        # Log the exception or handle it if necessary
        return str(exc)

@app.task(bind=True, name='task_management.celery_app.summarizer', time_limit=420, soft_time_limit=300)
def summarizer(self, *args, **kwargs):
    try:
        status = execute_script("scripts/summarizer/summarizer_groq_llama8b.py")
        return status
    except Exception as exc:
        # Log the exception or handle it if necessary
        return str(exc)

@app.task(bind=True, name='task_management.celery_app.tagging', time_limit=420, soft_time_limit=300)
def tagging(self, *args, **kwargs):
    try:
        status = execute_script("scripts/tagging/tagging_groq_llama8b.py")
        return status
    except Exception as exc:
        # Log the exception or handle it if necessary
        return str(exc)


@app.task(name='task_management.celery_app.execute_additional_tasks')
def execute_additional_tasks():
    task_chain = chain(
        scraper.s(),
        summarizer.s(),
        tagging.s()
    )
    task_chain.apply_async()

@app.task(name='task_management.celery_app.check_execute_additional_tasks')
def check_execute_additional_tasks():
    if 'execute_additional_tasks' not in task_queue:
        task_queue.append('execute_additional_tasks')

@app.task(name='task_management.celery_app.process_task_queue')
def process_task_queue():
    if task_queue:
        task_name = task_queue.pop(0)
        if task_name == 'execute_additional_tasks':
            execute_additional_tasks.delay()
