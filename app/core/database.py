import boto3
from boto3.dynamodb.conditions import Key, Attr

aws_access_key = "AKIA3RWDXTFSIADMEAPE"
aws_secret_access_key = "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"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')



def create_user(user):
    table = dynamodb.Table('users')
    response = table.put_item(Item=user)
    return response

def upload_browsing_data(history,user_id):
    table = dynamodb.Table('history')
    for item in history:
        item["user_id"] = user_id
        item["favourite"] = False
        table.put_item(Item=item)
    return True


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


