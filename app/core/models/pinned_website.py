import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import uuid

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def get_pinned_website(user_id):
    table = dynamodb.Table('pinned_websites')
    response = table.scan(
        FilterExpression="user_id = :user_id",
        ExpressionAttributeValues={
            ":user_id": user_id
        }
    )
    return response['Items']

def add_to_pinned_websites(user_id, domain_name, order):
    table = dynamodb.Table('pinned_websites')
    item = {
        'user_id': user_id,
        'domain_name': domain_name,
        'order': order,
        'id':  str(uuid.uuid4())
    }
    response = table.put_item(Item=item)
    return response
