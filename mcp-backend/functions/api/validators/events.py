"""Validation schemas for event endpoints."""

EVENT_ID_QUERY_SCHEMA = {
    "id": {
        "required": True,
        "types": str,
        "error": "Missing event ID",
    }
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
    "membershipFee": {"required": False, "types": (int, float)},
    "active": {"required": False, "types": bool},
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
    "membershipFee": {"required": False, "types": (int, float)},
    "active": {"required": False, "types": bool},
    "purchaseMode": {"required": False, "types": str},
}

DELETE_EVENT_SCHEMA = {
    "id": {"required": True, "types": str},
}

UPLOAD_EVENT_PHOTO_SCHEMA = {
    "eventId": {"required": True, "types": str},
    "image": {"required": True, "types": str},
}
