

from app import create_app
import os
app, celery = create_app()
app.app_context().push()

environment = os.environ.get("APPLICATION_ENV", "LOCAL")

if __name__ == '__main__':
    if environment == "production":
        app.run()
    else:
        app.run(host='0.0.0.0', debug=True, port=5001)
        
