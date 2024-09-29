from flask import Blueprint, current_app, request, jsonify
from app.core.modules.auth import get_jwt_token
from werkzeug.local import LocalProxy
from .auth_views import *
from ..models.user import *
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.controllers.history import *

core = Blueprint("core", __name__)
logger = LocalProxy(lambda: current_app.logger)


@core.route("/get-user/<string:slug>", methods=["GET"])
def get_mongo_user(slug, **kwargs):
    """Retrieve user information by slug."""
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400

    response = find_by_slug(slug)
    return jsonify(response), 200


@core.route("/create-user", methods=["POST"])
def create_user():
    """Create a new user or return existing user information."""
    data = request.get_json()
    signup = data.get("signup", False)
    stage = data.get("stage")
    slug = data.get("slug", "")
    code = data.get("code")

    # Verify user info from the token
    user_info_from_google = id_token.verify_oauth2_token(
        code, google_requests.Request(), os.environ.get("GOOGLE_CLIENT_ID")
    )

    if not all([code, stage is not None, user_info_from_google]):
        return jsonify({"error": "Missing required parameters"}), 400

    if signup:
        user = find_by_address(user_info_from_google["email"])
        if user:
            user["token"] = get_jwt_token(user["slug"], user_info_from_google["email"])
            return jsonify(user), 200
        else:
            # Create a new user
            user = User(
                user_info_from_google["email"],
                slug,
                stage,
                user_info_from_google["name"],
                user_info_from_google["picture"],
            )
            response = user.save(signup)
            if slug == "":
                slug = response["slug"]
            response["email"] = user_info_from_google["email"]
            response["token"] = get_jwt_token(slug, user_info_from_google["email"])
            return jsonify(response), 201  # 201 Created
    else:
        # Case 3: User does not exist and signup is false
        user = find_by_address(user_info_from_google["email"])
        print(user)
        if user is None:
            return jsonify({"message": "Please sign up"}), 200
        else:
            user["token"] = get_jwt_token(user["slug"], user_info_from_google["email"])
            return jsonify(user), 200


@core.route("/update-user/<string:slug>", methods=["PUT"])
@token_required
def update_user(slug, **kwargs):
    """Update user information."""
    data = request.get_json()
    name = data.get("name")
    verified = data.get("verified")
    about = data.get("about")
    pfp = data.get("pfp")
    content_tags = data.get("content_tags")
    identity_tags = data.get("identity_tags")
    badges = data.get("badges")
    profile_metadata = data.get("profile_metadata")

    if not all(
        [
            address,
            name,
            slug,
            about,
            pfp,
            content_tags,
            identity_tags,
            badges,
            profile_metadata,
        ]
    ):
        return jsonify({"error": "Missing required parameters"}), 400

    address = find_by_address_slug(slug)
    if not address:
        return jsonify({"error": "User is not found"}), 401

    address_from_token = kwargs.get("user_data")["payload"]["publicAddress"]
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "User is not authorized"}), 401

    response = update_by_slug(
        address,
        slug,
        name,
        verified,
        about,
        pfp,
        content_tags,
        identity_tags,
        badges,
        profile_metadata,
    )
    return jsonify(response), 200


@core.route("/update-settings/<string:slug>", methods=["PUT"])
@token_required
def update_user_settings(slug, **kwargs):
    """Update user settings."""
    data = request.get_json()
    settings = data.get("settings")
    stage = data.get("stage")

    if not all([slug, settings, stage]):
        return jsonify({"error": "Missing required parameters"}), 400

    address = find_by_address_slug(slug)
    if not address:
        return jsonify({"error": "User is not found"}), 401

    address_from_token = kwargs.get("user_data")["payload"]["publicAddress"]
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "User is not authorized"}), 401

    response = update_settings_by_slug(slug, settings, stage, "")
    return jsonify(response), 200


@core.route("/check_slug", methods=["GET"])
def check_slug():
    """Check if a slug is already in use."""
    slug = request.args.get("slug")
    if not slug:
        return jsonify({"error": "Slug parameter is missing."}), 400

    slugs = fetch_user_slug()
    return jsonify({"result": slug not in slugs}), 200


@core.route("/update-mint-count/<string:slug>", methods=["PUT"])
def update_mint_count(slug):
    """Update the mint count for a user."""
    if not slug:
        return jsonify({"error": "Slug parameter is missing."}), 400

    try:
        update_minting_count(slug)
        return jsonify({"message": f"Mint count updated for user {slug}"}), 200
    except Exception as e:
        print(f"Error while updating mint count: {str(e)}")
        return jsonify({"error": "Error while updating mint count"}), 500


@core.route("/update-about/<string:slug>", methods=["PUT"])
@token_required
def update_about_for_user(slug, **kwargs):
    try:
        data = request.get_json()
        about = data.get("about")

        if not all([slug, about]):
            return jsonify({"error": f"Missing required parameters"}), 400

        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "User is not found"}), 401
        address_from_token = kwargs.get("user_data")["payload"]["publicAddress"]
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "User is not authorized"}), 401

        response = update_about_by_slug(slug, about)
        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": f"Error while updating about for user {slug}"}), 500


@core.route("/top-users", methods=["GET"])
def get_top_users():
    """Fetch the top users based on Kleo points."""
    try:
        limit = request.args.get("limit", default=20, type=int)
        leaderboard = get_top_users_by_kleo_points(limit)
        return jsonify(leaderboard), 200
    except Exception as e:
        logger.error(f"Error in get_top_users: {str(e)}")
        return jsonify({"error": "An error occurred while fetching top users"}), 500


@core.route("/rank/<string:slug>", methods=["GET"])
def get_user_rank(slug):
    """Get the rank of a user by slug."""
    result, status_code = calculate_rank(slug)
    return jsonify(result), status_code
