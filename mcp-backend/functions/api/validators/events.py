"""Validation schemas for event endpoints."""


def _validate_status(value):
    if not isinstance(value, str):
        return False
    return value in {"coming_soon", "active", "sold_out", "ended"}

EVENT_ID_QUERY_SCHEMA = {
    "id": {
        "required": False,
        "types": str,
        "error": "Missing event ID",
    },
    "slug": {
        "required": False,
        "types": str,
        "error": "Missing event slug",
    },
}

CREATE_EVENT_SCHEMA = {
    "title": {"required": True, "types": str},
    "location": {"required": True, "types": str},
    "locationHint": {"required": True, "types": str},
    "date": {"required": True, "types": str},
    "startTime": {"required": True, "types": str},
    "endTime": {"required": False, "types": str},
    "price": {"required": False, "types": (int, float)},
    "fee": {"required": False, "types": (int, float)},
    "status": {"required": False, "types": str, "validator": _validate_status},
    "purchaseMode": {"required": False, "types": str},
}

UPDATE_EVENT_SCHEMA = {
    "id": {"required": True, "types": str},
    "title": {"required": False, "types": str},
    "location": {"required": False, "types": str},
    "locationHint": {"required": False, "types": str},
    "date": {"required": False, "types": str},
    "startTime": {"required": False, "types": str},
    "endTime": {"required": False, "types": str},
    "price": {"required": False, "types": (int, float)},
    "fee": {"required": False, "types": (int, float)},
    "status": {"required": False, "types": str, "validator": _validate_status},
    "purchaseMode": {"required": False, "types": str},
}

DELETE_EVENT_SCHEMA = {
    "id": {"required": True, "types": str},
}

UPLOAD_EVENT_PHOTO_SCHEMA = {
    "eventId": {"required": True, "types": str},
    "image": {"required": True, "types": str},
}
