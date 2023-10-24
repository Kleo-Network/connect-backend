import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import uuid

from ..models.aws_session import dynamodb


def get_domain_string(user_id, domain_string):
    table = dynamodb.Table('domains')
    response = table.scan(
    FilterExpression="contains(#dm, :val_domain)",
    ExpressionAttributeNames={"#dm": "domain"},
    ExpressionAttributeValues={':val_domain': domain_string}
    )
    print(response['Items'])
    for item in response['Items']:
        item["pinned"] = check_pinned_website(user_id, item["domain"])
        item["icon"] = "https://www.google.com/s2/favicons?domain={}m&sz=48".format(item["domain"])
    return response['Items']


def get_pinned_website(user_id):
    table = dynamodb.Table('pinned_websites')
    response = table.scan(
        FilterExpression="user_id = :user_id",
        ExpressionAttributeValues={
            ":user_id": user_id
        }
    )
    for item in response['Items']:
        item["icon"] = "https://www.google.com/s2/favicons?domain={}m&sz=48".format(item["domain"])
    return response['Items']

def remove_pinned_website(user_id,domain):
    table = dynamodb.Table('pinned_websites')
    response = table.delete_item(
            Key={
                'user_id': user_id,
                'domain': domain  # your primary key column name and value
            }
        )
    return response
def check_pinned_website(user_id, domain):
    table = dynamodb.Table('pinned_websites')
    response = table.get_item(Key={'user_id': user_id, 'domain': domain})
    if 'Item' in response:
        return True
    else:
        return False

def add_to_pinned_websites(user_id, domain_name, order, title):
    table = dynamodb.Table('pinned_websites')
    item = {
        'user_id': user_id,
        'domain': domain_name,
        'order': order,
        'title': title
    }
    response = table.put_item(Item=item)
    return response
