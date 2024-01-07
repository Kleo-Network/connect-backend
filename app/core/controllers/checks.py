import boto3
import time
from datetime import datetime, timezone, timedelta
from ..models.aws_session import dynamodb
from decimal import Decimal

def get_midnights_between_epochs(start_epoch, end_epoch):
    # Convert the start and end epochs to datetime objects
    start_date = datetime.datetime.fromtimestamp(start_epoch)
    end_date = datetime.datetime.fromtimestamp(end_epoch)
    # Normalize start_date to midnight
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    # Iterate over each day and yield the midnight epoch
    current_date = start_date
    while current_date < end_date:
        yield int(current_date.timestamp())
        current_date += datetime.timedelta(days=1)


def check_user_graphs_fn(user_id, startTime, endTime):
    table = dynamodb.Table('processor')
    epoch_iterator = get_midnights_between_epochs(startTime, endTime)
    returnEpochs = {}
    for epoch in epoch_iterator:
        response = table.get_item(
                Key={
                'user_id': user_id,
                'date': Decimal(epoch)
            })
        returnEpochs[epoch] = 'Item' in response
    return returnEpochs    

    # Check if the item exists
    

# Example usage
