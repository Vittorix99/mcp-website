import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ExternalErrorLogger")


def _normalize_message(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        primary = value.get("error") or value.get("message")
        details = []

        invalid_emails = value.get("invalid_emails")
        if isinstance(invalid_emails, list) and invalid_emails:
            details.append("Invalid: " + ", ".join(str(item) for item in invalid_emails))

        non_existing = value.get("non_existing_subscribers")
        if isinstance(non_existing, list) and non_existing:
            details.append("Missing: " + ", ".join(str(item) for item in non_existing))

        if isinstance(primary, str) and (primary or details):
            return " | ".join([primary, *details] if primary else details)

    try:
        return json.dumps(value, ensure_ascii=True, default=str)
    except Exception:
        return str(value)


def log_external_error(
    service: str,
    message: str,
    operation: Optional[str] = None,
    source: Optional[str] = None,
    status_code: Optional[int] = None,
    payload: Any = None,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "error",
) -> None:
    """Non-blocking logger for external service failures."""
    try:
        details: Dict[str, Any] = {
            "service": service,
            "message": _normalize_message(message),
            "operation": operation,
            "source": source,
            "status_code": status_code,
            "payload": payload,
            "context": context,
            "severity": severity or "error",
        }
        compact = json.dumps(
            {key: value for key, value in details.items() if value is not None},
            ensure_ascii=True,
            default=str,
        )
        logger.error("%s", compact)
    except Exception as exc:
        logger.debug("Failed to serialize external error log: %s", exc)
