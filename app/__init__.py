import logging.config
from os import environ

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .core.celery.main import make_celery
from .config import config as app_config

import os

redis_url = os.environ.get("REDIS_URL", "redis")
redis_port = os.environ.get("REDIS_PORT", "6379")

def create_app():
    # loading env vars from .env file
    load_dotenv()
    APPLICATION_ENV = get_environment()
    logging.config.dictConfig(app_config[APPLICATION_ENV].LOGGING)
    app = Flask(app_config[APPLICATION_ENV].APP_NAME)
    app.config.from_object(app_config[APPLICATION_ENV])
    # app.config["CELERY_CONFIG"] = {
    #     "broker_url": f"redis://{redis_url}:{redis_port}",
    #     "result_backend": f"redis://{redis_url}:{redis_port}"
    # } 
    app.config["CELERY_CONFIG"] = {
        "broker_url": f"redis://localhost:{redis_port}",
        "result_backend": f"redis://localhost:{redis_port}"
    }    
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    celery = make_celery(app)
    celery.set_default()
    

    from .core.views.user_views import core as core_user
    from .core.views.auth_views import core as core_auth
    from .core.views.card_views import core as core_card
    from .core.views.history_views import core as core_history
    from .core.views.static_views import core as core_static_card
    app.register_blueprint(
        core_user,
        name="user_api",
        url_prefix='/api/v1/core/user'
    )
    app.register_blueprint(
        core_auth,
        name="auth_api",
        url_prefix='/api/v1/core/auth'
    )
    app.register_blueprint(
        core_card,
        name="card_api",
        url_prefix='/api/v1/core/cards'
    )
    app.register_blueprint(
        core_history,
        name="history_api",
        url_prefix='/api/v1/core/history'
    )
    app.register_blueprint(
        core_static_card,
        name="static_card_api",
        url_prefix='/api/v1/core/static-card'
    )
    return app, celery


def get_environment():
    return environ.get('APPLICATION_ENV') or 'development'
