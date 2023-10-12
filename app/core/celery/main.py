from celery import Celery 
from datetime import timedelta

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])
    celery.conf.beat_schedule = {
    'hello-world-every-4-seconds': {
        'task': 'tasks.hello_world',
        'schedule': timedelta(seconds=4),
        },
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery