"""Bounded HTTP completion records without request data or root logger changes."""
from functools import wraps
import json
from time import perf_counter
from uuid import uuid4

from flask import after_this_request, request
from werkzeug.exceptions import HTTPException

from config import get_runtime_settings


_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def observe_http_request(handler):
    @wraps(handler)
    def observed(*args, **kwargs):
        started = perf_counter()
        request_id = str(uuid4())
        method = request.method if request.method in _METHODS else "OTHER"
        recorded = False

        def emit(status):
            nonlocal recorded
            if recorded:
                return
            recorded = True
            try:
                print(json.dumps({
                    "event": "http_request_completed",
                    "severity": "ERROR" if status >= 500 else "WARNING" if status >= 400 else "INFO",
                    "environment": get_runtime_settings().environment.value,
                    "function": handler.__name__,
                    "request_id": request_id,
                    "method": method,
                    "status_code": status,
                    "duration_ms": max(0, round((perf_counter() - started) * 1000, 3)),
                }, separators=(",", ":")), flush=True)
            except Exception:
                # Observability failure must not replace a response or the original exception.
                pass

        @after_this_request
        def completed(response):
            if not recorded:
                response.headers["X-Request-ID"] = request_id
                emit(response.status_code)
            return response

        try:
            return handler(*args, **kwargs)
        except HTTPException:
            raise  # Flask finalizes these with their actual HTTP status.
        except Exception:
            emit(500)
            raise

    return observed
