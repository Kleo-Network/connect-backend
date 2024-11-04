from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize Flask app with a descriptive name
    app = Flask("KLEO-NETWORK")

    # Enable Cross-Origin Resource Sharing (CORS) for all API routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register all the blueprints
    register_blueprints(app)

    return app


def register_blueprints(app):
    """
    Function to register all blueprints to the Flask app.
    Keeps the create_app function clean and modular.
    """

    # Import blueprints
    from .core.views.user_views import core as core_user

    # Register blueprints with proper versioned URL prefixes
    app.register_blueprint(core_user, name="user_api", url_prefix="/api/v1/core/tasks")
   