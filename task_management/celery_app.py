from celery import Celery
from celery.schedules import crontab
from config.config_loader import load_config

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
            'task': 'tasks.fetch_urls_task',
            'schedule': crontab(minute='*/2'),
        },
        'execute-all-tasks-every-30-minutes': {
            'task': 'tasks.execute_additional_tasks',
            'schedule': crontab(minute='*/30'),
        },
    }
)

@app.task
def update_status(task_name, task_statuses, task_status):
    # Your code to update status
    pass