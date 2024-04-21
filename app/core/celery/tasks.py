from ..modules.history import create_pending_cards
from ..modules.graph_data import *
from ..controllers.history import *
from ..models.history import *
from ..models.user import *

from celery import shared_task
from celery.contrib.abortable import AbortableTask
import time
from urllib.parse import urlparse
import json
from decimal import Decimal
from datetime import datetime, timedelta, timezone

# create a task to take json and send it for training. 
@shared_task(bind=True, base=AbortableTask)
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
    
######################### pending card creation celery task ###############################
        
@shared_task(bind=True, base=AbortableTask)
def create_pending_card(self, user_slug):
    user = find_by_slug(user_slug)
    if user:    
        last_published_at = user['last_cards_marked']
        time_difference_days = (datetime.now().timestamp() - last_published_at) / (60 * 60 * 24)
        #if time_difference_days < 4:
        create_pending_cards(user_slug)
        
        next_execution = datetime.now(timezone.utc) + timedelta(minutes=30)
        create_pending_card.apply_async([user_slug], eta=next_execution)
        
    
        
        
# @shared_task(base=AbortableTask)
# def process_pinned_domain_items_for_graph(user, domain):
#     process_items_pinned_data(user, domain)
# @celery.task(name='core.tasks.get_icon_from_url')
# def getIcon(item, user_id):
#     extracted = tldextract.extract(item["url"])
#     domain = "{}.{}".format(extracted.domain, extracted.suffix)
#     item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
    
#     return True

    