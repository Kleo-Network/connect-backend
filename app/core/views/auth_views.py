from flask import Blueprint, current_app, request, jsonify
import jwt
import os
from eth_account.messages import encode_defunct
import random
from ..controllers.user import *
from werkzeug.local import LocalProxy
from functools import wraps
from web3 import Web3
import nacl.signing
import nacl.encoding
import base58

core = Blueprint('core', __name__)
w3 = Web3() 

logger = LocalProxy(lambda: current_app.logger)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[0]
            except IndexError:
                return jsonify({'message': 'Bearer token malformed.'}), 401

        if not token:
            return jsonify({'message': 'Token is missing.'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, os.environ.get('SECRET', 'default_secret'), algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid or expired.'}), 401

        # Add the user data to the kwargs
        kwargs['user_data'] = data
        return f(*args, **kwargs)

    return decorated

@core.route('/get_user', methods=["POST"])
def get_user():
    data = request.json 
    address = data['address']
    signup = data.get('signup', False)
    user = check_user_and_return(address,signup)
    if user is not None:
        return jsonify(user), 200
    else: 
        return jsonify({"404": "User not found"}),200

@core.route('/get_user_privacy', methods=["POST"])
@token_required
def get_user_privacy(**kwargs):
    data = request.json 
    address = data['address']
    signup = data.get('signup', False)
    self = address == kwargs.get('user_data')['payload']['publicAddress']
    user = check_user_and_return(address,signup,self)
    if user is not None:
        return jsonify(user), 200
    else: 
        return jsonify({"404": "User not found"}),200

    
@core.route('/check_invite_code', methods=["GET"])
def check_invite_code_api():
    invite = request.args.get('code')
    if check_invite_code(invite):
        return jsonify("OK"), 200
    else:
        return jsonify(error='Bad Request'),201

@core.route('/test_api', methods=['GET'])
@token_required
def test_api(**kwargs):
    public_address = kwargs.get('user_data')['payload']['publicAddress']
    return jsonify({'message': f'Test API accessed by user with public address: {public_address}'})
    
@core.route('/create_jwt_authentication', methods=["POST"])
def create():
    data = request.json
    signature = data['signature']
    public_address = data['publicAddress']
    chain = data['chain']
    signup = data.get('signup', False)
    if not signature or not public_address or not chain:
        return jsonify(error='Request should have signature and publicAddress'), 400

    
    user = check_user_and_return(public_address, signup)
    
    if not user:
        return jsonify(error=f'User with publicAddress {public_address} is not found in database'), 401
    msg = f"I am signing my one-time nonce: {str(user['nonce'])}"

    if chain == "ethereum":
        print("ethereum")
        message = encode_defunct(text=msg)
        recovered_address = w3.eth.account.recover_message(message, signature=signature)
        print(recovered_address)
        print(public_address)
        if recovered_address.lower() != public_address.lower():
            return jsonify(error='Signature verification failed'), 401

        
        update_user_nonce(user['id'], random.randint(1, 10000))

        try:
            # Your config should be set in the environment or some config files
            SECRET = os.environ.get('SECRET', 'default_secret')
            ALGORITHM = os.environ.get('ALGORITHM', 'HS256')

            access_token = jwt.encode({'payload': {'publicAddress': public_address}},
                                  SECRET, algorithm=ALGORITHM)
            return jsonify(accessToken=access_token)
        except Exception as e:
            return jsonify(error=str(e)), 500
    elif chain == "solana":
        public_key_bytes = base58.b58decode(public_address)
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
        signature_bytes = bytes(signature)
        verify_key.verify(msg.encode(), signature_bytes)
        update_user_nonce(user['id'], random.randint(1, 10000))        
        try:
            SECRET = os.environ.get('SECRET', 'default_secret')
            ALGORITHM = os.environ.get('ALGORITHM', 'HS256')

            access_token = jwt.encode({'payload': {'id': user["id"], 'publicAddress': public_address}},
                                  SECRET, algorithm=ALGORITHM)
            return jsonify(accessToken=access_token)
        except Exception as e:
            return jsonify(error=str(e)), 500