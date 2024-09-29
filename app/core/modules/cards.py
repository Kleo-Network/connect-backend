from ..models.history import get_history_count
from ...celery.tasks import *


def history_count(slug, count):
    actual_count = get_history_count(slug)
    print("history_count:")
    print(actual_count)
    return actual_count > count
