from ..models.history import get_history_count
from ..models.celery_tasks import get_celery_tasks_by_slug
from ..models.pending_cards import (
    get_pending_card,
    delete_pending_card,
    get_pending_card_count,
)
from ..models.published_cards import PublishedCard
from ...celery.tasks import *


def process_slug(slug):
    return create_pending_card.s({"message": "create cards from admin API"}, slug)


def get_pending_cards_count(slug, count):
    actual_count = get_pending_card_count(slug)
    print("pending cards")
    print(actual_count)
    if actual_count == 0:
        return True
    else:
        return False


def history_count(slug, count):
    actual_count = get_history_count(slug)
    print("history_count:")
    print(actual_count)
    return actual_count > count


def move_pending_to_published(slug):
    pending_cards = get_pending_card(slug)
    moved_count = 0
    print("pending cards")
    print(pending_cards)
    for card in pending_cards:
        # Create a new PublishedCard object
        published_card = PublishedCard(
            slug=slug,
            type=card["cardType"],
            content=card["content"],
            tags=card["tags"],
            urls=card["urls"],
            metadata=card["metadata"],
            category=card["category"],
            timestamp=card["date"],
        )

        # Save the published card
        published_card.save()

        print(delete_pending_card(slug, card["id"]))
        moved_count += 1

    return moved_count
