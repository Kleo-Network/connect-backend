from kombu import Queue
from app.config import get_settings as app_settings
import os
from kombu.utils.url import safequote
import urllib

settings = app_settings()


class BaseSettings:
    """Celery Configuration"""

    broker_url =  os.environ.get("RABBITMQ_URL","amqps://")
    result_backend = f"redis://redis:6379"
    broker_transport = "amqp"
    task_default_queue = "default"
    task_queues = (
        Queue("activity-classification"),
        Queue("default"),
        Queue("remove-pii"),
        Queue("send-email"),
    )
    broker_transport_options = {"region": "ap-south-1"}
    enable_remote_control = False
    worker_concurrency = 1
    include: list = ["app.celery.tasks"]
    broker_use_ssl = True
    broker_heartbeat = 60
    broker_login_method = "AMQPLAIN"
    broker_user = os.environ.get("RABBIT_MQ_USERNAME", "vaibhavgeek")
    broker_password = os.environ.get("RABBIT_MQ_PASSWORD", "adminKleoNetwork")


def get_settings():
    return BaseSettings()
