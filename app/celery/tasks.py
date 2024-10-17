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
def contextual_activity_classification(self, history_batch, address):
    # Store PII-removed content
    clean_contents = []
    pii_counts = []

    # Iterate through the batch of 100 history items
    for item in history_batch:
        # Remove PII and gather clean content
        pii_result = remove_pii(item["title"])
        clean_content = pii_result["updated_text"]
        pii_count = pii_result["pii_count"]

        # Store the cleaned content and PII count for later processing
        clean_contents.append(clean_content)
        pii_counts.append(pii_count)

    # Classify the batch of clean content
    activities = get_most_relevant_activity(clean_contents)

    # Iterate through each classified activity and save it along with history entries
    for idx, item in enumerate(history_batch):
        activity = activities[idx]
        print(f"Most relevant activity for item {idx} is {activity}")

        # Find the user by address
        user = find_by_address(address)

        if not user:
            print(f"User with address {address} not found")
            continue

        # Create a new History entry
        history_entry = History(
            address=address,
            url=item["url"],
            title=item["title"],
            visitTime=float(item["lastVisitTime"]),
            category=activity,
        )

        # Save the history entry to the database
        history_entry.save()

        print(
            f"Saved history entry for user {address}: {item['title']} - Activity: {activity}"
        )

        # Update the PII count and data quantity for the user
        text_size_in_bytes = len(clean_contents[idx].encode("utf-8"))
        user_updated = update_user_data_by_address(
            address, pii_counts[idx], text_size_in_bytes
        )

        if user_updated:
            print(f"Successfully updated PII count for user with address {address}")
        else:
            print(f"Failed to update PII count for user with address {address}")

    return activities


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
