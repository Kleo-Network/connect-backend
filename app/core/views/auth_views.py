from flask import Blueprint, current_app, request, jsonify
import jwt
import os
from eth_account.messages import encode_defunct
import random
from ..models.user import *
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

@core.route('/test_api', methods=['GET'])
@token_required
def test_api(**kwargs):
    public_address = kwargs.get('user_data')['payload']['publicAddress']
    return jsonify({'message': f'Test API accessed by user with public address: {public_address}'})
            
@core.route('/v2/create_jwt_authentication', methods=["POST"])
def create_jwt_for_slug():
    data = request.json
    slug = data['slug']
    public_address = data['publicAddress']
    
    address = find_by_address_slug(slug)
    
    if not address:
        return jsonify(error=f'User with publicAddress {public_address} is not found in database'), 401
    
    if address != public_address:
        return jsonify(error='Signature verification failed'), 401
    
    try:
        SECRET = os.environ.get('SECRET', 'default_secret')
        ALGORITHM = os.environ.get('ALGORITHM', 'HS256')

        access_token = jwt.encode({'payload': {'slug': slug, 'publicAddress': public_address}},
                                SECRET, algorithm=ALGORITHM)
        return jsonify(accessToken=access_token)
    except Exception as e:
            return jsonify(error=str(e)), 500