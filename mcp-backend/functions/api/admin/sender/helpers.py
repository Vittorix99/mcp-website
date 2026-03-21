from typing import Any, Dict, Optional

from services.sender.sender_service import SenderService

_sender_service: Optional[SenderService] = None


def get_sender_service() -> SenderService:
    global _sender_service
    if _sender_service is None:
        _sender_service = SenderService()
    return _sender_service


def get_payload(req) -> Dict[str, Any]:
    try:
        return req.get_json() or {}
    except Exception:
        return {}


def get_query_params(req) -> Dict[str, Any]:
    if not getattr(req, "args", None):
        return {}
    try:
        return req.args.to_dict(flat=True)
    except Exception:
        return dict(req.args)


def pick(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None
