from __future__ import annotations

import re
from typing import Any


_EMAIL_RE = re.compile(r"(?P<local>[A-Za-z0-9._%+\-]{1,64})@(?P<domain>[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=\-]+", re.IGNORECASE)
_LONG_SECRET_RE = re.compile(r"\b[A-Za-z0-9._~+/=\-]{32,}\b")
_SERVICE_ACCOUNT_PATH_RE = re.compile(r"(?:[A-Za-z]:)?(?:/[^,\s'\"\)]+)+service_account[^,\s'\"\)]*\.json")

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "service_account",
    "token",
)

_EMAIL_KEY_PARTS = (
    "email",
    "from_email",
    "reply_to",
    "to_email",
)


def mask_email(value: Any) -> str:
    raw = str(value or "")
    if "@" not in raw:
        return raw

    def _replace(match: re.Match[str]) -> str:
        local = match.group("local")
        domain = match.group("domain")
        prefix = local[:2] if len(local) > 2 else local[:1]
        return f"{prefix}***@{domain}"

    return _EMAIL_RE.sub(_replace, raw)


def redact_string(value: str) -> str:
    redacted = _SERVICE_ACCOUNT_PATH_RE.sub("[REDACTED_PATH]", value)
    redacted = _BEARER_RE.sub("Bearer [REDACTED]", redacted)
    redacted = _EMAIL_RE.sub(lambda match: mask_email(match.group(0)), redacted)
    return _LONG_SECRET_RE.sub("[REDACTED]", redacted)


def redact_sensitive(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return redact_string(value)

    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_str = str(key)
            key_lower = key_str.lower()
            if any(part in key_lower for part in _SENSITIVE_KEY_PARTS):
                sanitized[key] = "[REDACTED]"
            elif any(part in key_lower for part in _EMAIL_KEY_PARTS):
                sanitized[key] = mask_email(item)
            else:
                sanitized[key] = redact_sensitive(item)
        return sanitized

    if isinstance(value, (list, tuple, set)):
        return [redact_sensitive(item) for item in value]

    return redact_string(str(value))


def safe_id(value: Any) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    if len(raw) <= 8:
        return "[REDACTED]"
    return f"{raw[:4]}...{raw[-4:]}"
