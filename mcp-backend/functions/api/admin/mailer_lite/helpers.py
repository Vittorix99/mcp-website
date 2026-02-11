import json
from typing import Any, Dict, Optional

from services.mailer_lite import MailerLiteError


def get_payload(req) -> Dict[str, Any]:
    try:
        return req.get_json() or {}
    except Exception:
        return {}


def get_query_params(req) -> Dict[str, Any]:
    if not getattr(req, "args", None):
        return {}
    try:
        params = req.args.to_dict(flat=True)
    except Exception:
        params = dict(req.args)

    for key in ("limit", "page"):
        if key in params:
            try:
                params[key] = int(params[key])
            except (TypeError, ValueError):
                pass

    if "filter" in params and isinstance(params["filter"], str):
        raw = params["filter"].strip()
        if raw.startswith("{") or raw.startswith("["):
            try:
                params["filter"] = json.loads(raw)
            except json.JSONDecodeError:
                pass

    return params


def pick(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def handle_mailerlite_error(error: MailerLiteError):
    payload = {"error": "MailerLite request failed"}
    if error.payload is not None:
        payload["details"] = error.payload
    if error.status:
        payload["status"] = error.status
    return payload, error.status or 500
