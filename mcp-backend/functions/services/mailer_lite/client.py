import logging
import os
from typing import Any, Callable, Dict, Optional

import mailerlite as MailerLite

from config.external_services import MAILERLITE_API_KEY
from config.environment import load_environment

logger = logging.getLogger("MailerLiteClient")


class MailerLiteError(RuntimeError):
    def __init__(self, message: str, status: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


def filter_kwargs(data: Optional[Dict[str, Any]], allowed: set) -> Dict[str, Any]:
    if not data:
        return {}
    return {key: data[key] for key in allowed if key in data and data[key] is not None}


class MailerLiteClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        resolved_key = api_key or os.environ.get("MAILERLITE_API_KEY") or MAILERLITE_API_KEY
        if not resolved_key:
            load_environment()
            resolved_key = api_key or os.environ.get("MAILERLITE_API_KEY") or MAILERLITE_API_KEY
        self.api_key = resolved_key

        if not self.api_key:
            raise ValueError("MAILERLITE_API_KEY is missing")
        options = {"api_key": self.api_key}
        self.sdk = MailerLite.Client(options)

    def call(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error("MailerLite SDK error: %s", e)
            raise MailerLiteError(str(e)) from e
