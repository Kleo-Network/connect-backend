import boto3
from decimal import Decimal
from ..modules.history import single_url_request
import boto3
import os
from datetime import datetime, timedelta

AWS_ACCESS_KEY_ID = os.environ.get('API_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
# Initialize a session using Amazon DynamoDB credentials.
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Create DynamoDB resource.
dynamodb = session.resource('dynamodb')


def domain_exists_or_insert(domain):
    table = dynamodb.Table("domains")
    print(AWS_ACCESS_KEY_ID)
    print(AWS_SECRET_ACCESS_KEY)
    print(AWS_SECRET_ACCESS_KEY)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('domain').eq(domain)
    )
    
    if len(response['Items']) > 0:
        return response['Items'][0]
    else:
        category_group, category_description, category = single_url_request(domain)
        item =  {'domain': domain,
                'category_group': category_group,
                'category_description': category_description, 
                'category': category}
        table.put_item(Item=item)
        return item
        


def convert_floats_to_decimal(item):
    for key, value in item.items():
        if isinstance(value, float):
            item[key] = Decimal(str(value))
    return item
    
def check_user_authenticity(user_address_from_ui, user_address_from_header):
    return user_address_from_ui == user_address_from_header
# Example usage

def get_last_third_month_start_date():
    today = datetime.now()
    # Calculate the starting date of the last third month
    last_month_end_date = today.replace(day=1) - timedelta(days=1)
    last_to_last_month_end_date = last_month_end_date - timedelta(days=last_month_end_date.day)
    last_to_last_to_last_month_end_date = last_to_last_month_end_date.replace(day=1) - timedelta(days=1)
    starting_date_last_third_month = last_to_last_to_last_month_end_date.replace(day=1)
    
    return starting_date_last_third_month




