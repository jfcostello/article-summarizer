# task_management/celery_app.py
# This file configures a Celery application for task management, including periodic task scheduling and task execution chains - it determines when each task fires, and is responsible for triggering their execution. It defines tasks for fetching URLs, scraping content, summarizing articles, tagging articles, and managing the execution queue. The tasks are scheduled to run at specific intervals using Celery's beat scheduler.
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery, chain
from celery.schedules import crontab
from config.config_loader import load_config
import subprocess

# Load the configuration settings for the Celery app
config = load_config()
# Initialize the Celery app with the broker URL from the configuration
app = Celery('tasks', broker=config['celery']['broker_url'])

# Update Celery app configuration with result backend, serializers, timezone, and beat schedule
app.conf.update(
    result_backend=config['celery']['result_backend'],
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        # Runs fetch url task every 2 minutes
        'fetch-urls-every-2-minutes': {
            'task': 'task_management.celery_app.fetch_urls',
            'schedule': crontab(minute='*/2'),
        },
        # Sdds execute additional tasks (the remaining tasks) to a queue every 30 minutes
        'check-execute-additional-tasks-every-30-minutes': {
            'task': 'task_management.celery_app.check_execute_additional_tasks',
            'schedule': crontab(minute='*/30'),
        },
        # Checks what's in the queue and, if there is something, runs it every minute
        'process-task-queue-every-minute': {
            'task': 'task_management.celery_app.process_task_queue',
            'schedule': crontab(minute='*/1'),
        },
    }
)

task_queue = []

scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Runs the fetch_urls task. Looks for a return saying how many URLs were added. 
# If none, do nothing, if 1 or more, add execute_additional_tasks to the queue
@app.task(name='task_management.celery_app.fetch_urls')
def fetch_urls(**kwargs):  # Accept keyword arguments
    try:
        # Pass run_all_scripts to main.py (it will default to False if not provided)
        run_all_scripts = kwargs.get('run_all_scripts', False)
        result = subprocess.run([sys.executable, os.path.join(scripts_path, 'main.py'), 'fetch_urls', 
                                str(run_all_scripts)], capture_output=True, text=True)
        
        if result.returncode == 0:  # Success
            try:
                total_new_urls = int(result.stdout.strip()) 
            except ValueError:
                # Log an error - couldn't convert output to integer
                total_new_urls = 0  
        else:
            # Log an error - subprocess had a non-zero exit code
            total_new_urls = 0

        if total_new_urls > 0:
            print("DEBUG: Adding 'execute_additional_tasks' to the task queue")
            task_queue.append(('execute_additional_tasks',)) 

            return total_new_urls

    except Exception as exc:
        return str(exc)

# Runs the scraper task, has a fall back time limit where it will cut it off if still running
@app.task(bind=True, name='task_management.celery_app.scraper', time_limit=420, soft_time_limit=300)
def scraper(self, **kwargs):  # Accept keyword arguments
    try:
        # Pass run_all_scripts to main.py
        run_all_scripts = kwargs.get('run_all_scripts', False)
        result = subprocess.run([sys.executable, os.path.join(scripts_path, 'main.py'), 'scrape_content', 
                                str(run_all_scripts)], capture_output=True, text=True)
        return result.stdout
    except Exception as exc:
        return str(exc)

# Runs the summarizer task, has a fall back time limit where it will cut it off if still running
@app.task(bind=True, name='task_management.celery_app.summarizer', time_limit=420, soft_time_limit=300)
def summarizer(self, **kwargs):  # Accept keyword arguments
    try:
        # Pass run_all_scripts to main.py
        run_all_scripts = kwargs.get('run_all_scripts', False)
        result = subprocess.run([sys.executable, os.path.join(scripts_path, 'main.py'), 'summarize_articles', 
                                str(run_all_scripts)], capture_output=True, text=True)
        return result.stdout
    except Exception as exc:
        return str(exc)

# Runs the tagging task, has a fall back time limit where it will cut it off if still running
@app.task(bind=True, name='task_management.celery_app.tagging', time_limit=420, soft_time_limit=300)
def tagging(self, **kwargs):  # Accept keyword arguments
    try:
        # Pass run_all_scripts to main.py
        run_all_scripts = kwargs.get('run_all_scripts', False)
        result = subprocess.run([sys.executable, os.path.join(scripts_path, 'main.py'), 'tag_articles', 
                                str(run_all_scripts)], capture_output=True, text=True)
        return result.stdout
    except Exception as exc:
        return str(exc)

# Task for processing the task queue and executing additional tasks if present
# We use a queue for execute_additional_tasks always to prevent multiple instances running simultaniously, which could cause problems when adding things to the same row in our DB
@app.task(name='task_management.celery_app.process_task_queue')
def process_task_queue():
    print("DEBUG: process_task_queue function called.")
    if task_queue:
        print(f"DEBUG: Task queue contains: {task_queue}")
        # Get the task data (a tuple containing the task name and arguments)
        task_data = task_queue.pop(0)

        # Unpack the task name and arguments
        task_name, *task_args = task_data

        # Construct the fully qualified task name
        fully_qualified_task_name = f"task_management.celery_app.{task_name}"

        # Retrieve the Celery task function using the fully qualified name
        task_function = app.tasks.get(fully_qualified_task_name)

        if task_function:
            # Execute the task with the unpacked arguments
            task_function.delay(*task_args)
        else:
            print(f"ERROR: Task '{task_name}' not found.")

# @app.task(name='task_management.celery_app.trigger_queue_processing') # New task for manual trigger, this is for debugging
# def trigger_queue_processing():
    # process_task_queue.delay()  # Call the queue processing task

# Tasks that just chains the scraper, summarizer and tagging tasks together - executing them back to bakc. One task ending, with any status, triggers the next to run
@app.task(name='task_management.celery_app.execute_additional_tasks')
def execute_additional_tasks(run_all_scripts=False):
    task_chain = chain(
        scraper.s(run_all_scripts=run_all_scripts),
        summarizer.s(run_all_scripts=run_all_scripts),
        tagging.s(run_all_scripts=run_all_scripts)
    )
    task_chain.apply_async()

# Task for checking and adding 'execute_additional_tasks' to the queue if not present
# This is temporary. We want more complex logic where it will check if it has run at all in the last x minutes, if it hasn't, add to queue, if it has, do nothing
# Using run_all_scripts for now, so every 30 minutes we get a clean, full run with all backup scripts running
@app.task(name='task_management.celery_app.check_execute_additional_tasks')
def check_execute_additional_tasks(run_all_scripts=False):
    if 'execute_additional_tasks' not in task_queue:
        # Add the task name and arguments as a tuple to the queue
        task_queue.append(('execute_additional_tasks', run_all_scripts))