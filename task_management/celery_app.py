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
        'process-task-queue-every-minute': {
            'task': 'task_management.celery_app.process_task_queue',
            'schedule': crontab(minute='*/1'),
        },
        'add-additional-tasks-to-queue-every-30-minutes': {
            'task': 'task_management.celery_app.add_additional_tasks_to_queue',
            'schedule': crontab(minute='*/30'),
        },
    }
)

task_queue = []

@app.task(name='task_management.celery_app.fetch_urls')
def fetch_urls():
    result = subprocess.run([sys.executable, "scripts/main.py", "fetch_urls"], capture_output=True, text=True)
    if result.returncode == 0:
        try:
            total_new_urls = int(result.stdout.strip())
            if total_new_urls > 0:
                task_queue.append('execute_additional_tasks')
            return total_new_urls
        except ValueError:
            return 0
    return 0

@app.task(bind=True, name='task_management.celery_app.scraper', time_limit=420, soft_time_limit=300)
def scraper(self):
    try:
        status = execute_script("scripts/main.py scrape_content")
        return status
    except Exception as exc:
        # Log the exception or handle it if necessary
        return str(exc)

@app.task(bind=True, name='task_management.celery_app.summarizer', time_limit=420, soft_time_limit=300)
def summarizer(self):
    try:
        status = execute_script("scripts/main.py summarize_articles")
        return status
    except Exception as exc:
        # Log the exception or handle it if necessary
        return str(exc)

@app.task(bind=True, name='task_management.celery_app.tagging', time_limit=420, soft_time_limit=300)
def tagging(self):
    try:
        status = execute_script("scripts/main.py tag_articles")
        return status
    except Exception as exc:
        # Log the exception or handle it if necessary
        return str(exc)

@app.task(name='task_management.celery_app.execute_additional_tasks')
def execute_additional_tasks():
    task_chain = chain(
        scraper.s(),
        summarizer.s(),
        tagging.s(),
        task_finished.s()
    )
    task_chain.apply_async()

@app.task(name='task_management.celery_app.task_finished')
def task_finished():
    pass

@app.task(name='task_management.celery_app.process_task_queue')
def process_task_queue():
    if len(task_queue) > 0:
        task_name = task_queue.pop(0)
        execute_additional_tasks.delay()

@app.task(name='task_management.celery_app.add_additional_tasks_to_queue')
def add_additional_tasks_to_queue():
    global last_execution_time

    if last_execution_time is None or (datetime.now() - last_execution_time) > timedelta(minutes=30):
        task_queue.append('execute_additional_tasks')
