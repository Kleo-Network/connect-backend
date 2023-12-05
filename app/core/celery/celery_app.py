from celery import Celery
from os import environ

celery = Celery(environ.get('APP_NAME') or 'flask-boilerplate')
