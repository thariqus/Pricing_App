import hmac
import os
from functools import wraps
from flask import request, Response


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = os.getenv("ADMIN_USERNAME", "")
        password = os.getenv("ADMIN_PASSWORD", "")
        auth = request.authorization

        if (
            user and password and auth
            and hmac.compare_digest(auth.username or "", user)
            and hmac.compare_digest(auth.password or "", password)
        ):
            return view(*args, **kwargs)

        return Response(
            "Admin login required", 401,
            {"WWW-Authenticate": 'Basic realm="Admin"'}
        )

    return wrapper