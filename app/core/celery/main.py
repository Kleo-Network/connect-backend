from .celery_app import celery

from celery import Celery 
from datetime import timedelta

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])
    celery.conf.beat_schedule = {
    'process-graphs-from-history': {
        'task': 'tasks.process_graph_data',
        'schedule': timedelta(minutes=3),
        },
    'update-new-graphs':{
        'task': 'tasks.update_new_history',
        'schedule': timedelta(minutes=5)
       }
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery