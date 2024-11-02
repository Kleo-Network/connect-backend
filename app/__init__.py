from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize Flask app with a descriptive name
    app = Flask("KLEO-NETWORK")

    # Enable Cross-Origin Resource Sharing (CORS) globally for all origins (*)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register all the blueprints
    register_blueprints(app)

    # Ensure correct headers are sent in the response
    @app.after_request
    def add_cors_headers(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"
        )
        return response

    return app


def register_blueprints(app):
    """
    Function to register all blueprints to the Flask app.
    Keeps the create_app function clean and modular.
    """

    # Import blueprints
    from .core.views.user_views import core as core_user
    from .core.views.user_v2_views import core as core_user_v2
    from .core.views.auth_views import core as core_auth
    from .core.views.history_views import core as core_history
    from .core.views.admin_views import core as admin_views

    # Register blueprints with proper versioned URL prefixes
    app.register_blueprint(core_user, name="user_api", url_prefix="/api/v1/core/user")
    app.register_blueprint(
        core_user_v2, name="user_api_v2", url_prefix="/api/v2/core/user"
    )
    app.register_blueprint(core_auth, name="auth_api", url_prefix="/api/v1/core/auth")
    app.register_blueprint(
        core_history, name="history_api", url_prefix="/api/v1/core/history"
    )
    app.register_blueprint(
        admin_views, name="admin_api", url_prefix="/api/v1/core/admin"
    )
