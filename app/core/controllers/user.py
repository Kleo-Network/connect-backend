import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json

from models.aws_session import dynamodb


def create_user(user):
    table = dynamodb.Table('users')
    response = table.put_item(Item=user)
    return response

def get_entire_profile(user_id):
    table = dynamodb.Table('users')
    response = table.query(
        KeyConditionExpression="user_id = :user_id",
        ExpressionAttributeValues={
            ":user_id": user_id
        }
    )
    items = response['Items']
    return items[0] if items else None
