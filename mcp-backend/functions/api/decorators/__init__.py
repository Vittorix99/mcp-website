from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

import firebase_admin.auth as fb_auth
from firebase_functions import https_fn
from flask import jsonify

from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .active_event import require_active_event


def public_endpoint(*, methods: Iterable[str]):
    allowed_methods = tuple(method.upper() for method in methods)

    def decorator(handler: Callable):
        @https_fn.on_request(cors=cors, region=region)
        @wraps(handler)
        def wrapped(req, *args, **kwargs):
            if req.method.upper() not in allowed_methods:
                return jsonify({"error": "Invalid method"}), 405
            return handler(req, *args, **kwargs)

        return wrapped

    return decorator


def admin_endpoint(*, methods: Iterable[str]):
    allowed_methods = tuple(method.upper() for method in methods)

    def decorator(handler: Callable):
        @https_fn.on_request(cors=cors, region=region)
        @require_admin
        @wraps(handler)
        def wrapped(req, *args, **kwargs):
            if req.method.upper() not in allowed_methods:
                return jsonify({"error": "Invalid method"}), 405
            return handler(req, *args, **kwargs)

        return wrapped

    return decorator


def member_endpoint(*, methods: Iterable[str]):
    """Decorator for member-authenticated endpoints.

    Verifies the Firebase ID token from the Authorization header.
    Any valid Firebase Auth user is accepted (no admin claim required).
    Injects the decoded token into req.member_token (mirrors req.admin_token pattern).
    """
    allowed_methods = tuple(method.upper() for method in methods)

    def decorator(handler: Callable):
        @https_fn.on_request(cors=cors, region=region)
        @wraps(handler)
        def wrapped(req, *args, **kwargs):
            if req.method.upper() not in allowed_methods:
                return jsonify({"error": "Invalid method"}), 405

            auth_header = req.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Authorization token missing"}), 401

            id_token = auth_header.split("Bearer ", 1)[1].strip()
            try:
                decoded_token = fb_auth.verify_id_token(id_token)
            except Exception:
                return jsonify({"error": "Invalid or expired token"}), 401

            req.member_token = decoded_token
            return handler(req, *args, **kwargs)

        return wrapped

    return decorator


__all__ = ["require_active_event", "public_endpoint", "admin_endpoint", "member_endpoint"]
