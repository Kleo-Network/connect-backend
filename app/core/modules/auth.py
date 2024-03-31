import os
from flask import jsonify
import jwt
from app.core.models.user import find_by_address_slug


def get_jwt_token(slug, email):
  address = find_by_address_slug(slug)
  if not address:
    return
  
  if address != email:
    return
  
  try:
    SECRET = os.environ.get('SECRET', 'default_secret')
    ALGORITHM = os.environ.get('ALGORITHM', 'HS256')

    access_token = jwt.encode({'payload': {'slug': slug, 'publicAddress': email}},
                            SECRET, algorithm=ALGORITHM)
    return access_token
  except Exception as e:
    return 