"""Bounded HTTP completion records without request data or root logger changes."""
from contextvars import ContextVar
from functools import wraps
import json
from time import perf_counter
from uuid import uuid4

from flask import after_this_request, request
from werkzeug.exceptions import HTTPException

from config import get_runtime_settings


_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
_current_request_id = ContextVar("http_request_id", default=None)


def _status(value):
    return value if isinstance(value, int) and 100 <= value <= 599 else None


def timed_dependency(provider, operation, call, classify):
    """Run `call` unchanged and log only its duration, status and outcome category.

    `classify(result)` returns (status_code, "success" | "error").
    """
    started = perf_counter()
    status, outcome = None, "exception"
    try:
        result = call()
        outcome = "error"
        try:
            status, outcome = classify(result)
        except Exception:
            pass  # A classification failure must never replace a valid result.
        return result
    except Exception as error:
        status = _status(getattr(error, "response_code", None))
        raise
    finally:
        try:
            status = _status(status)
            print(json.dumps({
                "event": "dependency_completed",
                "severity": "ERROR" if outcome == "exception" else "WARNING" if outcome == "error" else "INFO",
                "environment": get_runtime_settings().environment.value,
                "provider": provider,
                "operation": operation,
                "request_id": _current_request_id.get(),
                "status_code": status,
                "outcome": outcome,
                "duration_ms": max(0, round((perf_counter() - started) * 1000, 3)),
            }, separators=(",", ":")), flush=True)
        except Exception:
            # Observability failure must not replace a result or the original exception.
            pass


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

        token = _current_request_id.set(request_id)
        try:
            return handler(*args, **kwargs)
        except HTTPException:
            raise  # Flask finalizes these with their actual HTTP status.
        except Exception:
            emit(500)
            raise
        finally:
            _current_request_id.reset(token)

    return observed
