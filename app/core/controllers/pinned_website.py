import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import uuid

from ..models.aws_session import dynamodb


def get_domain_string(domain_string):
    table = dynamodb.Table('domains')
    response = table.scan(
    FilterExpression="contains(#dm, :val_domain)",
    ExpressionAttributeNames={"#dm": "domain"},
    ExpressionAttributeValues={':val_domain': domain_string}
    )
    return response['Items']


def get_pinned_website(user_id):
    table = dynamodb.Table('pinned_websites')
    response = table.scan(
        FilterExpression="user_id = :user_id",
        ExpressionAttributeValues={
            ":user_id": user_id
        }
    )
    return response['Items']

def add_to_pinned_websites(user_id, domain_name, order, title):
    table = dynamodb.Table('pinned_websites')
    item = {
        'user_id': user_id,
        'domain_name': domain_name,
        'order': order,
        'title': title,
        'id':  str(uuid.uuid4())
    }
    response = table.put_item(Item=item)
    return response
