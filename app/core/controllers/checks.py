import boto3
import time
from datetime import datetime, timezone, timedelta
from ..models.aws_session import dynamodb
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from flask import Flask, request, jsonify
from botocore.exceptions import ClientError


table = dynamodb.Table('processor')
history = dynamodb.Table('history')
users = dynamodb.Table('users')

def update_user_privacy(user_id, privacy_settings):
    try:
        response = users.update_item(
            Key={'id': user_id},
            UpdateExpression="SET privacy = :val",
            ExpressionAttributeValues={
                ':val': privacy_settings
            },
            ReturnValues="UPDATED_NEW"
        )
        return jsonify({'message': 'Privacy settings updated successfully', 'response': response}), 200
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

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

def calculate_processed_percentage(startTime, endTime, user_id):
    processor_table = dynamodb.Table('processor')

    # Get midnights between the start and end times
    epoch_iterator = get_midnights_between_epochs(startTime, endTime)
    total_days = 0
    processed_days = 0

    for epoch in epoch_iterator:
        total_days += 1
        response = processor_table.get_item(
            Key={'user_id': user_id, 'date': Decimal(epoch)}
        )
        if 'Item' in response:
            processed_days += 1

    # Calculate and return the percentage
    return (processed_days / total_days) * 100 if total_days > 0 else 0


def check_history_counts(user_id, startTime, endTime):
    response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) & 
                                   Key('visitTime').between(Decimal(startTime), Decimal(endTime))
    )
    
    if response['Items']:
        return True
    else:
        return False  # No items found after retrying


def check_user_graphs_fn(user_id, startTime, endTime):
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
