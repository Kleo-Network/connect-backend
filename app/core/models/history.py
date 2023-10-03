import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import random
from collections import defaultdict

# AWS Initialization
aws_access_key = "YOUR_AWS_ACCESS_KEY"
aws_secret_access_key = "YOUR_AWS_SECRET_ACCESS_KEY"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def record_exists(id, user_id):
    table = dynamodb.Table('history')
    response = table.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    return 'Items' in response and len(response['Items']) > 0

def upload_browsing_data(item, user_id):
    table = dynamodb.Table('history')
    item["user_id"] = user_id
    item["favourite"] = False
    item["id"] = str(random.randint(1, 10000000))
    item = json.loads(json.dumps(item), parse_float=Decimal)
    res = table.put_item(Item=item)
    return True

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

def query_history(user_id, filters):
    table = dynamodb.Table('history')
    key_condition = Key('user_id').eq(user_id)
    conditions = [Attr(attr).eq(value) for attr, value in filters]
    filter_expression = conditions[0]
    for condition in conditions[1:]:
        filter_expression = filter_expression & condition
    response = table.query(
        KeyConditionExpression=key_condition,
        FilterExpression=filter_expression
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

def get_grpah_query(user_id, fromEpoch, toEpoch, divisions):
    table = dynamodb.Table('history')
    fromEpoch = Decimal(fromEpoch)
    toEpoch = Decimal(toEpoch)
    divisions = Decimal(divisions)
    response = table.scan(
        FilterExpression="user_id = :user_id AND #visitTime BETWEEN :fromEpoch AND :toEpoch",
        ExpressionAttributeNames={
            "#visitTime": "visitTime",
        },
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":fromEpoch": fromEpoch,
            ":toEpoch": toEpoch
        }
    )
    items = response['Items']
    division_length = (toEpoch - fromEpoch) / divisions
    results = defaultdict(dict)
    for item in items:
        division_index = int((int(item["visitTime"]) - fromEpoch) / division_length)
        category = item['category']
        if category not in results[division_index]:
            results[division_index][category] = []
        results[division_index][category].append(item)
    return results
