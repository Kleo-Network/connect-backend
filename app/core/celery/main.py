from celery import Celery 
from datetime import timedelta

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])
    celery.conf.beat_schedule = {
    'hello-world-every-4-seconds': {
        'task': 'tasks.process_graph_data',
        'schedule': timedelta(seconds=30),
        },
    'update-new-graph-data':{
        'task': 'tasks.update_new_history',
        'schedule': timedelta(minutes=4)
       }
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery