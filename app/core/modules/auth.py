import os
import jwt


def get_jwt_token(wallet, slug):
    try:
        SECRET = os.environ.get("SECRET", "default_secret")
        ALGORITHM = os.environ.get("ALGORITHM", "HS256")

        payload = {"payload": {"slug": slug, "publicAddress": wallet}}

        access_token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
        return access_token
    except Exception as e:
        pass