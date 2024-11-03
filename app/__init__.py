from dotenv import load_dotenv
from flask import Flask,jsonify
from flask_cors import CORS

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded


def create_app():
    load_dotenv()

    app = Flask("KLEO-NETWORK")

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )
    @app.errorhandler(RateLimitExceeded)
    def rate_limit_handler(e):
        return jsonify(error="Rate limit exceeded. Please try again later."), 429

    register_blueprints(app, limiter)

    return app


def register_blueprints(app, limiter):
    """
    Function to register all blueprints to the Flask app.
    Keeps the create_app function clean and modular.
    """
    from .core.views.user_v2_views import core as core_user_v2
    
    limiter.limit("100 per hour")(core_user_v2)
    app.register_blueprint(
        core_user_v2, name="user_api_v2", url_prefix="/api/v2/core/user"
    )
