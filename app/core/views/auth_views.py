from flask import Blueprint, current_app, request, jsonify
import jwt
import os
from eth_account.messages import encode_defunct
import random
from ..controllers.user import *
from werkzeug.local import LocalProxy
from functools import wraps
from web3 import Web3 
core = Blueprint('core', __name__)
w3 = Web3() 

logger = LocalProxy(lambda: current_app.logger)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Bearer token malformed.'}), 401

        if not token:
            return jsonify({'message': 'Token is missing.'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid or expired.'}), 401

        # Add the user data to the kwargs
        kwargs['user_data'] = data
        return f(*args, **kwargs)

    return decorated

@core.route('/create_jwt_authentication', methods=["POST"])
def create():
    data = request.json
    signature = data['signature']
    public_address = data['publicAddress']

    if not signature or not public_address:
        return jsonify(error='Request should have signature and publicAddress'), 400

    user = check_user_and_return(public_address)
    print(user)
    if not user:
        return jsonify(error=f'User with publicAddress {public_address} is not found in database'), 401
    #msg = f"I am signing my one-time nonce: {str(user['nonce'])}"
    msg = f"I am signing my one-time nonce: 1"


    message = encode_defunct(text=msg)

    recovered_address = w3.eth.account.recover_message(message, signature=signature)
    print(recovered_address)
    if recovered_address.lower() != public_address.lower():
        return jsonify(error='Signature verification failed'), 401

    update_user_nonce(user['address'], random.randint(1, 10000))

    try:
        # Your config should be set in the environment or some config files
        SECRET = os.environ.get('SECRET', 'default_secret')
        ALGORITHM = os.environ.get('ALGORITHM', 'HS256')

        access_token = jwt.encode({'payload': {'id': user["id"], 'publicAddress': public_address}},
                                  SECRET, algorithm=ALGORITHM)
        return jsonify(accessToken=access_token)
    except Exception as e:
        return jsonify(error=str(e)), 500