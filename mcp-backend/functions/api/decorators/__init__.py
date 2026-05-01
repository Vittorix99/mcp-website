from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

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


__all__ = ["require_active_event", "public_endpoint", "admin_endpoint"]
