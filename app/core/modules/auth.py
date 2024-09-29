import os
import jwt
from flask import jsonify
from app.core.models.user import find_by_address_slug


def get_jwt_token(slug, email):
    """Generate a JWT token for a given user identified by slug and email."""

    # Fetch the user's address using the provided slug
    address = find_by_address_slug(slug)

    # Check if the user exists and if the email matches
    if not address:
        return jsonify({"error": "User not found"}), 404
    if address != email:
        return jsonify({"error": "Email does not match"}), 403

    try:
        # Retrieve secret and algorithm from environment variables
        SECRET = os.environ.get("SECRET", "default_secret")
        ALGORITHM = os.environ.get("ALGORITHM", "HS256")

        # Create the payload for the JWT
        payload = {"payload": {"slug": slug, "publicAddress": email}}

        # Encode the JWT token
        access_token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
        return access_token
    except Exception as e:
        # Log the exception or return a specific error message
        print(f"Error creating JWT token: {str(e)}")
        return jsonify({"error": "Could not create token"}), 500
