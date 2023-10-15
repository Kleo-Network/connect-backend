# aws_session.py

import boto3
from  .constants import *

# Initialize a session using Amazon DynamoDB credentials.
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Create DynamoDB resource.
dynamodb = session.resource('dynamodb')
