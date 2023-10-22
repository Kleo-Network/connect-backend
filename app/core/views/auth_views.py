from flask import Blueprint, current_app, request
import jwt
import os
from eth_utils import to_hex, from_wei, to_wei
from eth_account import Account
import random
from ..controllers.user import *
from werkzeug.local import LocalProxy

core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)

@core.route('/create_jwt_authentication', methods=["GET"])
def create():
    data = request.json
    signature = data.get('signature')
    public_address = data.get('publicAddress')

    if not signature or not public_address:
        return jsonify(error='Request should have signature and publicAddress'), 400

    #user = User.find_by_public_address(public_address)
    #if not user:
     #   return jsonify(error=f'User with publicAddress {public_address} is not found in database'), 401

    #msg = f"I am signing my one-time nonce: {user.nonce}"
    #msg_hash = to_wei(msg, "ether")

    #recovered_address = Account.recover_message(msg_hash, signature=signature)

    #if recovered_address.lower() != public_address.lower():
    #    return jsonify(error='Signature verification failed'), 401

    #user.nonce = random.randint(1, 10000)
    #user.save()

    try:
        # Your config should be set in the environment or some config files
        SECRET = os.environ.get('SECRET', 'default_secret')
        ALGORITHM = os.environ.get('ALGORITHM', 'HS256')

        access_token = jwt.encode({'payload': {'id': user.id, 'publicAddress': public_address}},
                                  SECRET, algorithm=ALGORITHM)
        return jsonify(accessToken=access_token)
    except Exception as e:
        return jsonify(error=str(e)), 500