from ..models.history import get_history_count
from ..models.celery_tasks import get_celery_tasks_by_slug
from ...celery.tasks import *
from ..models.pending_cards import get_pending_card_count

def process_slug(slug):
    return create_pending_card.s({"message": "create cards from admin API"}, slug)
    

def get_pending_cards_count(slug, count):
    actual_count = get_pending_card_count(slug)
    print("pending cards")
    print(actual_count)
    return actual_count < count

def history_count(slug, count):
    actual_count = get_history_count(slug)
    print("history_count:")
    print(actual_count)
    return actual_count > count