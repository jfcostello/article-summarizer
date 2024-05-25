from celery import Celery
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
)
