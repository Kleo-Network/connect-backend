import boto3
import time
from datetime import datetime, timezone
from ..models.aws_session import dynamodb
from decimal import Decimal

def get_midnight_epoch():
    # Get the current date with the time set to midnight
    midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Convert the midnight time to epoch
    midnight_epoch = int(midnight.replace(tzinfo=timezone.utc).timestamp())
    return midnight_epoch

def check_user_graphs_fn(user_id):
    today_epoch_midnight = get_midnight_epoch()
    table = dynamodb.Table('processor')

    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'date': Decimal(today_epoch_midnight)
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
