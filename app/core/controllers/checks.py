import boto3
import time
from datetime import datetime, timezone
from ..models.aws_session import dynamodb
from decimal import Decimal

def get_midnight_epoch(days_ago=0):
    # Calculate the midnight epoch for 'days_ago' days before today
    date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    midnight = datetime.datetime(date.year, date.month, date.day)
    return int(midnight.timestamp())


def check_user_graphs_fn(user_id, counter):
    table = dynamodb.Table('processor')
    check_date_epoch = get_midnight_epoch(counter)
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'date': Decimal(check_date_epoch)
            }
        )
    except Exception as e:
        print(f"Error accessing DynamoDB: {e}")
        return False

    # Check if the item exists
    if 'Item' in response:
        return True
    else: 
        False

# Example usage
