import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery, chain
from celery.schedules import crontab
from config.config_loader import load_config
import subprocess
from datetime import datetime, timedelta

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
task_running = False
last_execution_time = None

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

@app.task(name='task_management.celery_app.scraper', time_limit=1800, soft_time_limit=1500)
def scraper():
    subprocess.run([sys.executable, "scripts/main.py", "scrape_content"], check=True)

@app.task(name='task_management.celery_app.summarizer', time_limit=1800, soft_time_limit=1500)
def summarizer():
    subprocess.run([sys.executable, "scripts/main.py", "summarize_articles"], check=True)

@app.task(name='task_management.celery_app.tagging', time_limit=1800, soft_time_limit=1500)
def tagging():
    subprocess.run([sys.executable, "scripts/main.py", "tag_articles"], check=True)

@app.task(name='task_management.celery_app.execute_additional_tasks')
def execute_additional_tasks():
    global task_running, last_execution_time
    task_running = True
    last_execution_time = datetime.now()

    scraper.apply_async(link=summarizer.s())
    summarizer.apply_async(link=tagging.s())
    tagging.apply_async(link=task_finished.s())

@app.task(name='task_management.celery_app.task_finished')
def task_finished():
    global task_running
    task_running = False

@app.task(name='task_management.celery_app.process_task_queue')
def process_task_queue():
    global task_queue, task_running

    if not task_running and len(task_queue) > 0:
        task_name = task_queue.pop(0)
        execute_additional_tasks.delay()

@app.task(name='task_management.celery_app.add_additional_tasks_to_queue')
def add_additional_tasks_to_queue():
    global last_execution_time

    if last_execution_time is None or (datetime.now() - last_execution_time) > timedelta(minutes=30):
        task_queue.append('execute_additional_tasks')