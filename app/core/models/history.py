import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import random
from collections import defaultdict
from ..modules.history import single_url_request
import time

# AWS Initialization
aws_access_key = "os.environ.get('AWS_ACCESS_KEY_ID')"
aws_secret_access_key = "os.environ.get('AWS_SECRET_ACCESS_KEY')"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def domain_exists_or_insert(domain):
    table = dynamodb.Table("domains")
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('domain').eq(domain)
    )
    
    if response['Items']:
        print(response['Items'])
        return response['Items'][0]
    else:
        category_group, category_description, category = single_url_request(domain)
        # Insert domain into the table
        item =  {'domain': domain,
                'category_group': category_group,
                'category_description': category_description, 
                'category': category}
        table.put_item(Item=item)
        return item
        

def record_exists(user_id, visitTime):
    table = dynamodb.Table('history')
    response = table.query(
       KeyConditionExpression=(
            Key('user_id').eq(str(user_id)) & 
            Key('visitTime').eq(Decimal(str(visitTime)))
        )
    )
    print(len(response['Items']))
    return 'Items' in response and len(response['Items']) > 0

def upload_browsing_data(item, user_id):
    try:
        table = dynamodb.Table('history')
        item["user_id"] = str(user_id)
        item["favourite"] = False
        item["hidden"] = False
        item = json.loads(json.dumps(item), parse_float=Decimal)
        res = table.put_item(Item=item)
        return True
    except:
        time.sleep(5)
        pass
        

def get_history(user_id, from_epoch, to_epoch, regex):
    table = dynamodb.Table('history')
    response = table.scan(
        FilterExpression="user_id = :user_id AND #lastVisitTime BETWEEN :start_date AND :end_date AND contains(#name_attr, :username)",
        ExpressionAttributeNames={
            "#lastVisitTime": "lastVisitTime",
            "#name_attr": "url"
        },
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":username": regex,
            ":start_date": Decimal(from_epoch),
            ":end_date": Decimal(to_epoch)
        }
    )
    return response['Items']

def delete_history_item(primary_id):
    table = dynamodb.Table('history')
    response = table.delete_item(Key={"item_id": primary_id })
    return response 

def add_to_favourites(item_id):
    table = dynamodb.Table('history')
    response = table.update_item(
        Key={
            'id': item_id
        },
        UpdateExpression="set isStarred = :d",
        ExpressionAttributeValues={
            ':d': True
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def get_favourites(user_id, domain_name):
    table = dynamodb.Table('history')
    response = table.scan(
        FilterExpression="user_id = :user_id AND contains(#url_params, :domain) AND isStarred = :fav",
        ExpressionAttributeNames={
            "#url_params": "url"
        },
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":domain": domain_name,
            ":fav": True
        }
    )
    return response['Items']

def get_summary(user_id, domain_name):
    table = dynamodb.Table('history')
    response = table.scan(
        FilterExpression="user_id = :user_id AND contains(#url_params, :domain)",
        ExpressionAttributeNames={
            "#url_params": "url"
        },
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":domain": domain_name
        }
    )
    return response['Items']

