import logging.config
from os import environ

from celery import Celery
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .config import config as app_config

celery = Celery(__name__)


def create_app():
    # loading env vars from .env file
    load_dotenv()
    APPLICATION_ENV = get_environment()
    logging.config.dictConfig(app_config[APPLICATION_ENV].LOGGING)
    app = Flask(app_config[APPLICATION_ENV].APP_NAME)
    app.config.from_object(app_config[APPLICATION_ENV])

    CORS(app, resources={r'/api/*': {'origins': '*'}})

    celery.config_from_object(app.config, force=True)
    # celery is not able to pick result_backend and hence using update
    celery.conf.update(result_backend=app.config['RESULT_BACKEND'])

    from .core.views.history_views import core as core_history
    from .core.views.pinned_views import core as core_pinned
    from .core.views.user_views import core as core_user
    
    app.register_blueprint(
        core_history,
        name="history_api",
        url_prefix='/api/v1/core/history'
    )
    app.register_blueprint(
        core_pinned,
        name="pinned_api",
        url_prefix='/api/v1/core/pinned'
    )
    app.register_blueprint(
        core_user,
        name="user_api",
        url_prefix='/api/v1/core/user'
    )
    return app


def get_environment():
    return environ.get('APPLICATION_ENV') or 'development'
