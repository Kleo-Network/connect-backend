#!/bin/bash

# Step 1: Format the entire project with Black
echo "Formatting the project with Black..."
black .

# Step 2: Set the environment variable for Flask to run in debug mode
export FLASK_ENV=development

# Step 3: Run the Flask app (from run.py) in debug mode
echo "Starting the Flask application..."
python run.py
