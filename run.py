import os
from app import create_app
from app.celery.utils import create_celery

app = create_app()
app.celery_app = create_celery()
celery = app.celery_app

environment = os.environ.get("APPLICATION_ENV", "LOCAL")

if __name__ == "__main__":
    if environment == "production":
        app.run()
    else:
        app.run(host="0.0.0.0", debug=True, port=5001)
