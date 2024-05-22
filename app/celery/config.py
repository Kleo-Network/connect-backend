from kombu import Queue
from app.config import get_settings as app_settings
import os
from kombu.utils.url import safequote
import urllib

settings = app_settings()

class BaseSettings:
    """Celery Configuration"""
    
    broker_url = "sqs://"

    result_backend  = f"redis://redis:6379"
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
    worker_concurrency = 1
    include: list = ['app.celery.tasks']

def get_settings():
    return BaseSettings()