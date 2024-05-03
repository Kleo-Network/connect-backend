from kombu import Queue
from app.config import get_settings as app_settings

settings = app_settings()

class BaseSettings:
    """Celery Configuration"""
    broker_url = f"sqs://"
    result_backend  = None
    broker_transport = "sqs"
    task_default_queue = "kleo-queue-1"
    task_queues = (
        Queue("kleo-queue-1"),
        Queue("kleo-queue-2"),
        Queue("create-cards"),
    )
    broker_transport_options = {
        'region': 'ap-south-1'
    }
    worker_concurrency = 4
    include: list = ['app.celery.tasks']

def get_settings():
    return BaseSettings()