from ..core.modules.history import create_pending_cards
from ..core.controllers.history import *
from ..core.models.history import *
from ..core.models.user import *
from ..core.models.celery_tasks import *
from ..core.models.visits import *


from celery import shared_task
from celery.contrib.abortable import AbortableTask
from time import sleep
from urllib.parse import urlparse
import json
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from pymongo.errors import ServerSelectionTimeoutError
import random
import requests

def send_telegram_message(slug, body):
    tg_token_api = os.environ.get('TELEGRAM_API_TOKEN')
    channel_id = "-1002178791722"  # The channel ID you provided

    subject = f'Acticity for Slug: {slug}'
    message = f'```{json.dumps(body, indent=2)}```'

    # Send the message
    telegram_api_url = f"https://api.telegram.org/bot{tg_token_api}/sendMessage"
    
    payload = {
        "chat_id": channel_id,
        "text": f"{subject}\n\n{message}",
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(telegram_api_url, json=payload)
        if response.status_code == 200:
            print(f"Telegram message sent successfully for slug: {slug}")
        else:
            print(f"Failed to send Telegram message for slug: {slug}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message for slug: {slug}. Error: {str(e)}")
        
@shared_task(bind=True, base=AbortableTask,ack_later=True, default_retry_delay=20, max_retries=2, queue="send-email")
def send_telegram_notification(self, slug, response):
    send_telegram_message(slug,response)

# upload history & categorize it properly
@shared_task(bind=True, base=AbortableTask,ack_later=True, default_retry_delay=20, max_retries=2, queue="upload-history")
def categorize_history(self, data): 
    chunk = data["chunk"]
    slug = data["slug"]
    
    print(f"chunk:{chunk}\nslug: {slug}\n")
    for item in chunk:
        domain = urlparse(item["url"]).netloc
        if domain is not None:
            domain_data = domain_exists_or_insert(domain)
            history = History(slug, item["title"], domain_data["category"], domain_data["category_group"], item["url"], domain, domain_data["category_description"], int(item['lastVisitTime']))     
            visit = Visits(slug, domain_data["category"], domain, int(item['lastVisitTime']))
            visit.save()
            history.save()
        
    if self.is_aborted():
        return 'Aborted'
    last_processed_timestamp = datetime.now().timestamp()
    return last_processed_timestamp
    
# create pending tasks celery task       
@shared_task(bind=True, base=AbortableTask,ack_later=True, default_retry_delay=20, max_retries=2, queue="create-pending-cards")
def create_pending_card(self, result, slug):
    user = find_by_slug(slug)
    # when a task is created send a email to vaibhav.dkm@gmail.com from vaibhavblogger@gmail with the slug that task is created. 
    if not user:
        print(f"User with slug {slug} not found.")
        return

    if user["first_time_user"]:
        set_signup_upload_by_slug(slug)

    try:
        history_response = process_user_history(result, slug, user.get('first_time_user', False))
        schedule_next_execution(result, slug, user.get('first_time_user', False), hours=23, minutes=0)
        send_telegram_notification.delay(slug, history_response)
    except ServerSelectionTimeoutError:
        print("MongoDB connection timeout error occurred.")
      

def process_user_history(result, slug, first_time_user):
    if get_history_count(slug) > 20:
        response_llm = create_pending_cards(slug)
        schedule_next_execution(result, slug, first_time_user, hours=23, minutes=0)
        return response_llm
    else:
        handle_no_history(result, slug, first_time_user)
        return

def handle_no_history(result, slug, first_time_user):
    schedule_next_execution(result, slug,first_time_user, hours=23, minutes=0)

def schedule_next_execution(result, slug, first_time_user, hours, minutes): 
    next_execution = datetime.now(timezone.utc) + timedelta(hours=hours, minutes=minutes)
    async_result = create_pending_card.apply_async(kwargs={'result': result, 'slug': slug}, eta=next_execution)
    
# @shared_task(bind=True, base=AbortableTask)
# def checking_next_task_schedule(self,name="next_task"):
#     print("This is to be executed every 10 seconds")
#     next_execution = datetime.now(timezone.utc) + timedelta(seconds=10)
#     a = checking_next_task_schedule.apply_async(eta=next_execution)
#     return a         
        
# @shared_task(base=AbortableTask)
# def process_pinned_domain_items_for_graph(user, domain):
#     process_items_pinned_data(user, domain)
# @celery.task(name='core.tasks.get_icon_from_url')
# def getIcon(item, user_id):
#     extracted = tldextract.extract(item["url"])
#     domain = "{}.{}".format(extracted.domain, extracted.suffix)
#     item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
    
#     return True

    