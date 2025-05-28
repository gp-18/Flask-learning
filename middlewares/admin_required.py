from functools import wraps

from flask import request

from middlewares.verify_token import token_required
from utils.response import failure


def admin_required(f):
    @token_required
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(request, "user", None)
        if not user or user.get("role") != "admin":
            return failure(message="Admin access required", status_code=403)
        return f(*args, **kwargs)

    return decorated
