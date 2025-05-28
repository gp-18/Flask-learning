from functools import wraps

import jwt
from flask import current_app as app
from flask import request

from utils.response import failure


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return failure(message="Authorization token is missing", status_code=401)

        try:
            if app.config["DB"].token_blacklist.find_one({"token": token}):
                return failure(message="Token has been revoked", status_code=401)

            decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            request.user = {
                "user_id": decoded.get("user_id"),
                "email": decoded.get("email"),
                "role": decoded.get("role"),
            }
        except jwt.ExpiredSignatureError:
            return failure(message="Token has expired", status_code=401)
        except jwt.InvalidTokenError:
            return failure(message="Invalid token", status_code=401)

        return f(*args, **kwargs)

    return decorated
