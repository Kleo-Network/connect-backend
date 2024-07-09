from ..core.modules.history import create_pending_cards
from ..core.controllers.history import *
from ..core.models.history import *
from ..core.models.user import *
from ..core.models.celery_tasks import CeleryTask
from celery import shared_task
from celery.contrib.abortable import AbortableTask
from time import sleep
from urllib.parse import urlparse
import json
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from pymongo.errors import ServerSelectionTimeoutError
import random
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
            history.save()
        
    if self.is_aborted():
        return 'Aborted'
    last_processed_timestamp = datetime.now().timestamp()
    return last_processed_timestamp
    
# create pending tasks celery task       
@shared_task(bind=True, base=AbortableTask,ack_later=True, default_retry_delay=20, max_retries=2, queue="create-pending-cards")
def create_pending_card(self, result, slug):
    user = find_by_slug(slug)
    if not user:
        print(f"User with slug {slug} not found.")
        return

    if user["first_time_user"]:
        set_signup_upload_by_slug(slug)

    last_published_at = user['last_cards_marked']
    time_difference_days = (datetime.now().timestamp() - last_published_at) / (86400)  # 86400 seconds in a day

    if time_difference_days > 4:
        print(f"Last published time for user with slug {slug} is greater than 4 days. Skipping card creation.")
        return

    try:
        process_user_history(result, slug)
    except ServerSelectionTimeoutError:
        print("MongoDB connection timeout error occurred.")
        
@shared_task(bind=True, base=AbortableTask,ack_later=True, default_retry_delay=20, max_retries=2, queue="create-pending-cards-2")
def force_create_pending_cards(self, slug):
    user = find_by_slug(slug)
    if user:
        max_delay = 30
        delay = 5
        while delay <= max_delay:
            try:
                if get_history_count(slug) > 15:
                    create_pending_cards(slug)
                    return
                else:
                    sleep(delay)
                    delay += 5
            except ServerSelectionTimeoutError:
                print("MongoDB connection timeout error occurred.")
                break
    else:
        print(f"User with slug {slug} not found.")   

def process_user_history(result, slug):
    celery = CeleryTask.save(slug: slug, task_id, type_: "regular", status: "created")
    if get_history_count(slug) > 0:
        create_pending_cards(slug)
        schedule_next_execution(result, slug, hours=0, minutes=10)
    else:
        handle_no_history(result, slug)

def handle_no_history(result, slug):
    schedule_next_execution(result, slug, hours=23, minutes=50)

def schedule_next_execution(result, slug, hours, minutes):
    next_execution = datetime.now(timezone.utc) + timedelta(hours=hours, minutes=minutes)
    create_pending_card.apply_async(kwargs={'result': result, 'slug': slug}, eta=next_execution)
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

    