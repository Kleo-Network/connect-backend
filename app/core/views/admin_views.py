from flask import Blueprint, jsonify, request
from ..models.user import get_all_users_with_count
from celery import current_app as current_celery_app
from ..modules.cards import history_count
from app.celery.tasks import *
from collections import defaultdict
import ast

core = Blueprint("core", __name__)


# Route to abort scheduled tasks for users
@core.route("/tasks/abort_scheduled", methods=["GET"])
def abort_scheduled_tasks():
    """Abort scheduled tasks for all users based on their slugs."""
    users = get_all_users_with_count()
    i = current_celery_app.control.inspect()
    scheduled_tasks = i.scheduled() or {}

    tasks_to_revoke = {}
    kept_tasks = {}

    # Identify tasks to revoke and keep
    for worker, tasks in scheduled_tasks.items():
        for task in tasks:
            task_slug = task["request"]["kwargs"].get("slug")
            if task_slug in [user["slug"] for user in users]:
                if task_slug not in kept_tasks:
                    kept_tasks[task_slug] = task
                else:
                    if task_slug not in tasks_to_revoke:
                        tasks_to_revoke[task_slug] = []
                    tasks_to_revoke[task_slug].append(task["request"]["id"])

    revoked_count = 0
    for slug, task_ids in tasks_to_revoke.items():
        for task_id in task_ids:
            try:
                current_celery_app.control.revoke(task_id, terminate=True)
                revoked_count += 1
            except Exception:  # Catch any exception for a revoked task
                pass

    return (
        jsonify(
            {
                "message": f"Aborted {revoked_count} tasks for all users",
                "kept_tasks": {
                    slug: task["request"]["id"] for slug, task in kept_tasks.items()
                },
            }
        ),
        200,
    )


# Route to inspect scheduled tasks
@core.route("/tasks/inspect_celery_tasks", methods=["GET"])
def inspect_scheduled_tasks():
    """Inspect currently scheduled tasks."""
    i = current_celery_app.control.inspect()
    scheduled_tasks = i.scheduled() or {}
    return jsonify({"tasks": list(scheduled_tasks.values())}), 200


# Route to update scheduled tasks based on user status
@core.route("/tasks/update_celery", methods=["POST"])
def update_celery():
    """Update Celery tasks for all users based on their status."""
    data = request.get_json()
    i = current_celery_app.control.inspect()
    scheduled_tasks = i.scheduled() or {}
    users = get_all_users_with_count()

    new_tasks_count = 0
    revoked_tasks_count = 0

    # Loop through each user
    for user in users:
        slug = user["slug"]
        has_sufficient_history = history_count(slug, 60)

        # If conditions are not met, revoke any existing tasks for this user
        revoked_count = revoke_user_tasks(slug, scheduled_tasks)
        revoked_tasks_count += revoked_count

    return (
        jsonify(
            {
                "success": True,
                "message": "Tasks updated for all users",
                "new_tasks_scheduled": new_tasks_count,
                "tasks_revoked": revoked_tasks_count,
            }
        ),
        200,
    )


def revoke_user_tasks(slug, scheduled_tasks):
    """Revoke existing tasks for a given user slug."""
    revoked_count = 0
    for worker, tasks in scheduled_tasks.items():
        for task in tasks:
            if (
                task["request"]["name"] == "app.celery.tasks.create_pending_card"
                and task["request"]["kwargs"].get("slug") == slug
            ):
                try:
                    current_celery_app.control.revoke(
                        task["request"]["id"], terminate=True
                    )
                    revoked_count += 1
                except Exception:  # Catch any exception for a revoked task
                    pass  # Task was already completed or doesn't exist
    return revoked_count


@core.route("/tasks/list_active_users", methods=["POST"])
def list_active_users_zero_pending():
    """List active users with no pending cards."""
    users = get_all_users_with_count()
    active_users_with_no_pending_cards = []
    for user in users:
        slug = user["slug"]
        if history_count(slug, 60):
            active_users_with_no_pending_cards.append(user["slug"])
    return jsonify(active_users_with_no_pending_cards), 200


@core.route("/tasks/list_users_active_history", methods=["POST"])
def list_active_users():
    """List active users with activity history."""
    users = get_all_users_with_count()
    active_users_with_no_pending_cards = []
    for user in users:
        slug = user["slug"]
        if history_count(slug, 60):
            active_users_with_no_pending_cards.append(user["slug"])
    return jsonify(active_users_with_no_pending_cards), 200


@core.route("/tasks/active_users", methods=["POST"])
def list_inactive_users():
    """List users with published card counts."""
    users = get_all_users_with_count()
    active_users_with_no_publishing_cards = []
    for user in users:
        slug = user["slug"]
        count = 0
        active_users_with_no_publishing_cards.append(
            {"slug": user["slug"], "count": count}
        )
    return jsonify(active_users_with_no_publishing_cards), 200


@core.route("/tasks/update_milestone", methods=["POST"])
def update_milestone():
    """Update a user's milestone and Kleo points."""
    data = request.get_json()

    # Extract input parameters
    address = data.get("address")
    mileStoneKey = data.get("mileStoneKey")
    kleoPoints = data.get("kleoPoints", 0)  # Default to 0 if not provided
    newValue = data.get("newValue")

    # Input validation
    if not address or not mileStoneKey or newValue is None:
        return (
            jsonify(
                {
                    "error": "Invalid input. Address, mileStoneKey, and newValue are required."
                }
            ),
            400,
        )

    # Find the user by address
    user = find_by_address(address)
    if not user:
        return jsonify({"error": f"User with address {address} not found."}), 404

    # Check if the milestone key exists
    milestones = user.get("milestones", {})
    if mileStoneKey not in milestones:
        return (
            jsonify({"error": f"Milestone key {mileStoneKey} not found in user data."}),
            400,
        )

    # Update the milestone value
    milestones[mileStoneKey] = newValue

    # Add kleoPoints to the user's current kleo_points
    current_kleo_points = user.get("kleo_points", 0)
    updated_kleo_points = current_kleo_points + kleoPoints

    # Update the user in the database
    updated_user = update_user_milestones_data_by_address(
        address, milestones, updated_kleo_points
    )

    if updated_user:
        return (
            jsonify(
                {
                    "message": "Milestone and Kleo points updated successfully",
                    "milestones": updated_user.get("milestones"),
                    "kleo_points": updated_user.get("kleo_points"),
                }
            ),
            200,
        )
    else:
        return jsonify({"error": "Failed to update user data."}), 500


@core.route("/getHistoryCounts/<userAddress>", methods=["GET"])
def get_all_history_count_for_address(userAddress):
    try:
        if not userAddress:
            return jsonify({"error": "Address is required"}), 400

        count = get_history_count(userAddress)
        if not count:
            return (
                jsonify({"error": "Can't find any history with this given address"}),
                200,
            )

        return jsonify({"Counts": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
