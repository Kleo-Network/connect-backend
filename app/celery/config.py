from kombu import Queue
from app.config import get_settings as app_settings
import os
from kombu.utils.url import safequote
import urllib

settings = app_settings()

class BaseSettings:
    """Celery Configuration"""
    
    broker_url = "amqps://b-046c127e-1a88-4235-ad47-21d8f04bc4f0.mq.ap-south-1.amazonaws.com:5671"
    result_backend  = f"redis://redis:6379"
    broker_transport = "amqp"
    task_default_queue = "create-pending-cards"
    task_queues = (
        Queue("create-pending-cards"),
        Queue("upload-history"),
        Queue("create-pending-cards-2"),
        Queue("send-email"),
    )
    broker_transport_options = {
        'region': 'ap-south-1'
    }
    enable_remote_control = False
    worker_concurrency = 1
    include: list = ['app.celery.tasks']
    broker_use_ssl = True
    broker_heartbeat = 60
    broker_login_method = 'AMQPLAIN'
    broker_user = os.environ.get('RABBIT_MQ_USERNAME','vaibhavgeek')
    broker_password = os.environ.get('RABBIT_MQ_PASSWORD', 'helloKleoNetwork')

def get_settings():
    return BaseSettings()