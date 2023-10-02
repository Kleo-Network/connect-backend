import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from decimal import Decimal
import random 
aws_access_key = "os.environ.get('AWS_ACCESS_KEY_ID')"
aws_secret_access_key = "os.environ.get('AWS_SECRET_ACCESS_KEY')"
aws_region = "ap-south-1"
import uuid

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def record_exists(id, user_id):
    table = dynamodb.Table('history')
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq(id) & boto3.dynamodb.conditions.Key('user_id').eq(user_id)
    )
    return 'Items' in response and len(response['Items']) > 0

def create_user(user):
    table = dynamodb.Table('users')
    response = table.put_item(Item=user)
    return response

def upload_browsing_data(item,user_id):
    table = dynamodb.Table('history')
    item["user_id"] = user_id
    item["favourite"] = False
    item["id"] = str(random.randint(1, 10000000))
    item = json.loads(json.dumps(item), parse_float=Decimal)

    print("start")
    res = table.put_item(Item=item)
    print(item)
    print("uploaded")
    return True

def get_history(user_id, from_epoch, to_epoch, regex):
    table = dynamodb.Table('history')
    response = table.query(
        KeyConditionExpression=(
            "user_id = :user_id AND #time_attr BETWEEN :start_date AND :end_date"
        ),
        FilterExpression="contains (#name_attr, :username)",
        ExpressionAttributeNames={
            "#time_attr": "visitTime",
            "#name_attr": "url"
        },
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":username": regex,
            ":start_date": from_epoch,
            ":end_date": to_epoch
        }
    )
    return response['Items']

def query_history(user_id, filters):
    table = dynamodb.Table('history')
    key_condition = Key('user_id').eq(user_id)
    conditions = []
    for attr, value in filters:
        condition = Attr(attr).eq(value)
        conditions.append(condition)
    
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

def get_pinned_website(user_id):
    table = dynamodb.Table('pinned_websites')
    
    # Query the table for the given user_id
    response = table.scan(
    FilterExpression="user_id = :user_id",
    ExpressionAttributeValues={
        ":user_id": user_id
    })
    
    # Return the items from the response
    return response['Items']

def add_to_pinned_websites(user_id, domain_name, order):
    """
    Add a new item to the 'pinned_websites' DynamoDB table.

    :param user_id: The user ID.
    :param domain_name: The domain name.
    :param order: The order as an integer.
    """
    table = dynamodb.Table('pinned_websites')
    
    item = {
        'user_id': user_id,
        'domain_name': domain_name,
        'order': order,
        'id':  str(uuid.uuid4())
    }
    
    response = table.put_item(Item=item)
    
    return response