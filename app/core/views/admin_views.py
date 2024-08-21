from flask import Blueprint, jsonify, current_app, request
from celery.result import AsyncResult
from .auth_views import token_required
from ..models.user import find_by_address_slug, get_all_users_with_count
from ..models.celery_tasks import get_celery_tasks_by_slug, update_celery_task_status, get_all_celery_tasks, CeleryTask
from celery import current_app as current_celery_app
import os
from ..modules.cards import process_slug, history_count, get_pending_cards_count, move_pending_to_published
from ..models.pending_cards import get_pending_card_count
from ..models.published_cards import count_published_cards
from celery import group
from functools import partial
from app.celery.tasks import *
from ..modules.history import create_pending_cards

core = Blueprint('core', __name__)

@core.route('/tasks/abort_scheduled', methods=['GET'])
def abort_scheduled_tasks():
    users = get_all_users_with_count()
    
    i = current_celery_app.control.inspect()
    scheduled_tasks = i.scheduled() or {}

    tasks_to_revoke = {}
    kept_tasks = {}

    for worker, tasks in scheduled_tasks.items():
        for task in tasks:
            task_slug = task['request']['kwargs'].get('slug')
            if task_slug in [user['slug'] for user in users]:
                if task_slug not in kept_tasks:
                    kept_tasks[task_slug] = task
                else:
                    if task_slug not in tasks_to_revoke:
                        tasks_to_revoke[task_slug] = []
                    tasks_to_revoke[task_slug].append(task['request']['id'])

    revoked_count = 0
    for slug, task_ids in tasks_to_revoke.items():
        for task_id in task_ids:
            try:
                current_celery_app.control.revoke(task_id, terminate=True)
                revoked_count += 1
            except TaskRevokedError:
                pass  # Task was already completed or doesn't exist

    return jsonify({
        "message": f"Aborted {revoked_count} tasks for all users",
        "kept_tasks": {slug: task['request']['id'] for slug, task in kept_tasks.items()}
    }), 200


@core.route('/tasks/inspect_celery_tasks', methods=['GET'])
def inspect_scheduled_tasks():
    i = current_celery_app.control.inspect()
    scheduled_tasks = i.scheduled() or {}
    return jsonify({"tasks": list(scheduled_tasks.values())}), 200

@core.route('/tasks/update_celery', methods=['POST'])
def update_celery():
    data = request.get_json()
    i = current_celery_app.control.inspect()
    scheduled_tasks = i.scheduled() or {}
    
    users = get_all_users_with_count()
        
    new_tasks_count = 0
    revoked_tasks_count = 0
    
    # Loop through each user
    for user in users:
        slug = user["slug"]
        
        # Check if the user's slug is not present in scheduled tasks    
        is_scheduled = is_slug_scheduled(slug, scheduled_tasks)
        
        # Check if user has no pending cards and history count > 60
        has_no_pending_cards = get_pending_cards_count(slug, 0)
        has_sufficient_history = history_count(slug, 60)
        
        # If the conditions are met, create a new task
        if has_no_pending_cards and has_sufficient_history:
            if not is_scheduled:
                print(f"{slug} to be executed")
                task = create_pending_card.apply_async(
                    kwargs={'result': 'Create Pending Card from ADMIN', 'slug': slug},
                    queue='create-pending-cards-2'
                )
                print(f"Scheduled task for slug: {slug}, task id: {task.id}")
                new_tasks_count += 1
        else:
            # If conditions are not met, revoke any existing tasks for this user
            revoked_count = revoke_user_tasks(slug, scheduled_tasks)
            revoked_tasks_count += revoked_count

    return jsonify({
        "success": True,
        "message": "Tasks updated for all users",
        "new_tasks_scheduled": new_tasks_count,
        "tasks_revoked": revoked_tasks_count
    }), 200

def revoke_user_tasks(slug, scheduled_tasks):
    revoked_count = 0
    for worker, tasks in scheduled_tasks.items():
        for task in tasks:
            if (task['request']['name'] == 'app.celery.tasks.create_pending_card' and
                task['request']['kwargs'].get('slug') == slug):
                try:
                    current_celery_app.control.revoke(task['request']['id'], terminate=True)
                    revoked_count += 1
                except TaskRevokedError:
                    pass  # Task was already completed or doesn't exist
    return revoked_count

def is_slug_scheduled(slug, scheduled_tasks):
    for worker_tasks in scheduled_tasks.values():
        for task in worker_tasks:
            if task['request']['name'] == 'app.celery.tasks.create_pending_card':
                if task['request']['kwargs'].get('slug') == slug:
                    return True
    return False

@core.route('/tasks/list_active_users', methods=['POST'])
def list_active_users_zero_pending():
    users = get_all_users_with_count()
    active_users_with_no_pending_cards = []
    for user in users:
        slug = user["slug"]
        if history_count(slug, 60) and get_pending_cards_count(slug, 0):
            active_users_with_no_pending_cards.append(user["slug"])
    return jsonify(active_users_with_no_pending_cards), 200


@core.route('/tasks/list_users_active_history', methods=['POST'])
def list_active_users():
    users = get_all_users_with_count()
    active_users_with_no_pending_cards = []
    for user in users:
        slug = user["slug"]
        if history_count(slug, 60):
            active_users_with_no_pending_cards.append(user["slug"])
    return jsonify(active_users_with_no_pending_cards), 200

@core.route('/tasks/active_users', methods=['POST'])
def list_inactive_users():
    users = get_all_users_with_count()
    active_users_with_no_publishing_cards = []
    for user in users:
        slug = user["slug"]
        count = count_published_cards(slug)
        active_users_with_no_publishing_cards.append({"slug": user["slug"], "count": count})
    return jsonify(active_users_with_no_publishing_cards), 200


@core.route('/tasks/single_cards_create', methods=['POST'])
def single_slug_card_create():
    data = request.get_json()
    slug = data["slug"]
    response_llm = create_pending_cards(slug)
    return jsonify({"success": "{} cards created".format(slug)}),200

@core.route('/tasks/move_pending_cards_published', methods=['POST'])
def move_pending_cards_to_published():
    users = get_all_users_with_count()
    moved_cards_count = 0
    for user in users:
        slug = user["slug"]
        pending_count = get_pending_card_count(slug)
        
        if pending_count > 0:
            moved_count = move_pending_to_published(slug)
            moved_cards_count += moved_count
            print(f"Moved {moved_count} cards for user {slug}")

    return jsonify({
        "message": "Successfully moved pending cards to published cards",
        "total_cards_moved": moved_cards_count
    }), 200

@core.route('/tasks/move_specific_pending_cards/<string:slug>', methods=['GET'])
def move_specific_pending_cards(slug):
    # Get query parameters for card IDs
    moved_count = move_pending_to_published(slug)

    return jsonify({
        "message": f"Successfully moved pending cards to published for user {slug}",
        "cards_moved": moved_count
    }), 200

@core.route('/tasks/pending_cards_count', methods=['GET'])
def get_all_pending_cards_count():
    users = get_all_users_with_count()
    pending_cards_count = {}

    for user in users:
        slug = user["slug"]
        count = get_pending_card_count(slug)
        pending_cards_count[slug] = count

    total_count = sum(pending_cards_count.values())

    return jsonify({
        "pending_cards_count": pending_cards_count,
        "total_pending_cards": total_count
    }), 200

@core.route('/tasks/get_top',methods=['GET'])
def get_top():
    users = get_all_users_with_count()
    result = []
    for user in users:
        count = count_published_cards(user["slug"])
        result.append({user["slug"]: count})

    return jsonify(result), 200