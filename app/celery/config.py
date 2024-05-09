from kombu import Queue
from app.config import get_settings as app_settings

settings = app_settings()

class BaseSettings:
    """Celery Configuration"""
    broker_url = f"sqs://"
    result_backend  = None
    broker_transport = "sqs"
    task_default_queue = "create-pending-cards"
    task_queues = (
        Queue("create-pending-cards"),
        Queue("upload-history"),
        Queue("create-pending-cards-2"),
    )
    broker_transport_options = {
        'region': 'ap-south-1'
    }
    worker_concurrency = 8
    include: list = ['app.celery.tasks']

def get_settings():
    return BaseSettings()