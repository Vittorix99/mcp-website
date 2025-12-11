"""Validation schemas for admin message endpoints."""

DELETE_MESSAGE_SCHEMA = {
    "message_id": {"required": True, "types": str, "error": "message_id è obbligatorio"},
}

REPLY_MESSAGE_SCHEMA = {
    "message_id": {"required": True, "types": str, "error": "message_id è obbligatorio"},
    "email": {"required": True, "types": str},
    "body": {"required": True, "types": str},
    "subject": {"required": False, "types": str},
}
