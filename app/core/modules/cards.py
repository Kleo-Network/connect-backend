from ..models.history import get_history_count
from ..models.celery_tasks import get_celery_tasks_by_slug
from ...celery.tasks import *

def process_slug(slug, min_count=0):
    count = get_history_count(slug)
    print(count)
    tasks = get_celery_tasks_by_slug(slug)
    
    if count > min_count and not tasks:
        return create_pending_card.s({"message": "create cards from admin API"}, slug)
    return None