import logging.config
from os import environ

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app():
    load_dotenv()
    app = Flask('KLEO-NETWORK')
    CORS(app, resources={r'/api/*': {'origins': '*'}})
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
    return app


# def get_environment():
#     return environ.get('APPLICATION_ENV') or 'development'
