from flask import Blueprint, jsonify, request
from ..models.user import get_all_users_with_count
from celery import current_app as current_celery_app
from app.celery.tasks import *
from collections import defaultdict
import ast

core = Blueprint("core", __name__)




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
