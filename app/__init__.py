from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize Flask app with a descriptive name
    app = Flask("KLEO-NETWORK")

    # Enable Cross-Origin Resource Sharing (CORS) for all API routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configure Redis for rate limiting
    app.config['REDIS_URL'] = "redis://localhost:6379"
    redis_client = redis.from_url(app.config['REDIS_URL'])

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,  # Rate limit by IP address
        default_limits=["200 per day", "50 per hour"],  # Default limits for all routes
        storage_uri=app.config['REDIS_URL'],
        strategy="fixed-window"  # Use fixed time windows for rate limiting
    )

    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            "error": "Rate limit exceeded",
            "retry_after": e.description
        }, 429

    # Register all the blueprints
    register_blueprints(app)

    return app


def register_blueprints(app):
    """
    Function to register all blueprints to the Flask app.
    Keeps the create_app function clean and modular.
    """

    # Import blueprints
    from .core.views.user_v2_views import core as core_user_v2

    # Register blueprints with proper versioned URL prefixes
    app.register_blueprint(
        core_user_v2, 
        name="user_api_v2", 
        url_prefix="/api/v2/core/user"
    )

    # Apply specific rate limits to blueprint endpoints
    limiter = app.extensions['limiter']

    # Example of applying different rate limits to different endpoints
    limiter.limit("30/minute")(core_user_v2, "/get-user-graph/<userAddress>")
    limiter.limit("20/minute")(core_user_v2, "/save-history")
    limiter.limit("5/minute")(core_user_v2, "/create-user")
    limiter.limit("10/minute")(core_user_v2, "/upload_activity_chart")
    limiter.limit("60/minute")(core_user_v2, "/top-users")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)