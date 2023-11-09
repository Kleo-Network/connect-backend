import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json

from ..models.aws_session import dynamodb

def check_invite_code(code):
    table = dynamodb.Table('invite_codes')
    response = table.get_item(Key={'code': code})
    if 'Item' in response:
        counter = response['Item']['count']
        response_update = table.update_item(Key={'code': code},
                          UpdateExpression="SET #count = :counter ",
                          ExpressionAttributeNames={'#count': 'count'},
                          ExpressionAttributeValues={
                              ':counter': counter - 1
                          },
                          ReturnValues="UPDATED_NEW")
        return True
    else:
        return False

def update_user_nonce(id, nonce):
    table = dynamodb.Table('users')
    response = table.update_item(
            Key={
                'address': id  # your primary key column name and value
            },
            UpdateExpression="SET nonce = :val",  # Update the 'nonce' attribute
            ExpressionAttributeValues={
                ':val': nonce  # value that 'nonce' will be set to
            },
            ReturnValues="UPDATED_NEW"  # returns the item attributes as they appear after the update
        )
    return response

def check_user_and_return(address):
    table = dynamodb.Table('users')
    response = table.get_item(Key={'address': address})
    if 'Item' in response:
        return response['Item']
    else:
        return None
    
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
