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
    default_retry_delay=20,
    max_retries=0,
    queue="activity-classification",
)
def contextual_activity_classification(self, content, address):
    # TODO: Please provide what to do with this activity.
    activity = get_most_relevant_activity(content)


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
