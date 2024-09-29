import os
from app import create_app
from app.celery.utils import create_celery

# Create Flask app and attach Celery instance
app = create_app()
app.celery_app = create_celery()
celery = app.celery_app

# Get the environment setting (default is 'LOCAL')
environment = os.environ.get("APPLICATION_ENV", "LOCAL")

if __name__ == "__main__":
    # Run the app in production or development mode based on the environment
    if environment == "production":
        app.run()
    else:
        app.run(host="0.0.0.0", debug=True, port=5001)
