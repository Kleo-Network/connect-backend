from app.celery.userDataComputation.activityClassification import (
    get_most_relevant_activity,
)
from app.celery.userDataComputation.pii import remove_pii
from ..core.controllers.history import *
from ..core.models.history import *
from ..core.models.user import *
from ..core.models.celery_tasks import *
from ..core.models.visits import *

from celery import shared_task
from celery.contrib.abortable import AbortableTask
import json
import requests


def send_telegram_message(slug, body):
    tg_token_api = os.environ.get("TELEGRAM_API_TOKEN")
    channel_id = "-1002178791722"  # The channel ID you provided

    subject = f"Activity for Slug: {slug}"
    message = f"```{json.dumps(body, indent=2)}```"

    # Send the message
    telegram_api_url = f"https://api.telegram.org/bot{tg_token_api}/sendMessage"

    payload = {
        "chat_id": channel_id,
        "text": f"{subject}\n\n{message}",
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(telegram_api_url, json=payload)
        if response.status_code == 200:
            print(f"Telegram message sent successfully for slug: {slug}")
        else:
            print(
                f"Failed to send Telegram message for slug: {slug}. Status code: {response.status_code}"
            )
    except Exception as e:
        print(f"Failed to send Telegram message for slug: {slug}. Error: {str(e)}")


@shared_task(
    bind=True,
    base=AbortableTask,
    ack_later=True,
    default_retry_delay=20,
    max_retries=2,
    queue="send-email",
)
def send_telegram_notification(self, slug, response):
    send_telegram_message(slug, response)


@shared_task(
    bind=True,
    base=AbortableTask,
    ack_later=True,
    default_retry_delay=1,
    max_retries=0,
    queue="activity-classification",
)
def contextual_activity_classification(self, item, address):
    # Get the activity classification
    print(item)

    # Remove PII first, then pass for classification.
    pii_result = remove_pii(item["title"])
    clean_content = pii_result["updated_text"]
    pii_count = pii_result["pii_count"]
    # Calculate the size of the clean_text in bytes
    text_size_in_bytes = len(clean_content.encode("utf-8"))

    activity = get_most_relevant_activity(clean_content)
    print(f"Most relevant activity is {activity}")
    # Find the user by address
    user = find_by_address(address)

    if not user:
        print(f"User with address {address} not found")
        return

    # Create a new History entry
    history_entry = History(
        address=address,
        url=item["url"],
        title=item["title"],
        visitTime=item["lastVisitTime"],
        category=activity,
    )

    # Save the history entry to the database
    history_entry.save()

    print(
        f"Saved history entry for user {address}: {item['title']} - Activity: {activity}"
    )

    # Update the pii_removed_count and total_data_quantity in the user table using the address
    user_updated = update_user_data_by_address(address, pii_count, text_size_in_bytes)

    if user_updated:
        print(f"Successfully updated PII count for user with address {address}")
    else:
        print(f"Failed to update PII count for user with address {address}")

    return activity


@shared_task(
    bind=True,
    base=AbortableTask,
    ack_later=True,
    default_retry_delay=20,
    max_retries=0,
    queue="remove-pii",
)
def remove_PII(self, content, address):
    clean_text = remove_pii(content)
