from flask import Blueprint, current_app, request, jsonify
import jwt
import os
from werkzeug.local import LocalProxy
from functools import wraps
from web3 import Web3

from app.core.models.user import find_by_address_slug

core = Blueprint("core", __name__)
w3 = Web3()
logger = LocalProxy(lambda: current_app.logger)


# Decorator to require token authentication for endpoints
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get the token from the Authorization header
        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]
            except IndexError:
                return jsonify({"message": "Bearer token malformed."}), 401

        if not token:
            return jsonify({"message": "Token is missing."}), 401

        try:
            # Decode the token
            data = jwt.decode(
                token, os.environ.get("SECRET", "default_secret"), algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token is expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token is invalid."}), 401
        except:
            return (
                jsonify(
                    {
                        "message": "Something went wrong while authenticating. Please try again."
                    }
                ),
                401,
            )

        # Add the user data to the kwargs
        kwargs["user_data"] = data
        return f(*args, **kwargs)

    return decorated


# Test API endpoint
@core.route("/test_api", methods=["GET"])
@token_required
def test_api(**kwargs):
    public_address = kwargs.get("user_data")["payload"]["publicAddress"]
    return jsonify(
        {"message": f"Test API accessed by user with public address: {public_address}"}
    )


# Endpoint to create JWT authentication for a user
@core.route("/v2/create_jwt_authentication", methods=["POST"])
def create_jwt_for_slug():
    data = request.json
    slug = data.get("slug")
    public_address = data.get("publicAddress")

    # Find user by address slug
    address = find_by_address_slug(slug)

    if not address:
        return (
            jsonify(
                error=f"User with publicAddress {public_address} is not found in database"
            ),
            401,
        )

    if address != public_address:
        return jsonify(error="Signature verification failed"), 401

    try:
        SECRET = os.environ.get("SECRET", "default_secret")
        ALGORITHM = os.environ.get("ALGORITHM", "HS256")

        # Create JWT token
        access_token = jwt.encode(
            {"payload": {"slug": slug, "publicAddress": public_address}},
            SECRET,
            algorithm=ALGORITHM,
        )
        return jsonify(accessToken=access_token)
    except Exception as e:
        return jsonify(error=str(e)), 500
