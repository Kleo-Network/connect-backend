import logging.config
from os import environ

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .core.celery.main import make_celery
from .config import config as app_config



def create_app():
    # loading env vars from .env file
    load_dotenv()
    APPLICATION_ENV = get_environment()
    logging.config.dictConfig(app_config[APPLICATION_ENV].LOGGING)
    app = Flask(app_config[APPLICATION_ENV].APP_NAME)
    app.config.from_object(app_config[APPLICATION_ENV])
    app.config["CELERY_CONFIG"] = {"broker_url": "redis://localhost:6379", "result_backend": "redis://localhost:6379"}
    
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    celery = make_celery(app)
    celery.set_default()
    
    
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
    return app, celery


def get_environment():
    return environ.get('APPLICATION_ENV') or 'development'
