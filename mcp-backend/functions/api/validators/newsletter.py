"""Validation helpers for newsletter admin endpoints."""

from typing import Any, Dict

UPDATE_NEWSLETTER_SCHEMA = {
    "id": {"required": True, "types": str},
    "email": {"required": False, "types": str},
    "active": {"required": False, "types": bool},
    "source": {"required": False, "types": str},
}

NEWSLETTER_ID_QUERY_SCHEMA = {
    "id": {"required": True, "types": str, "error": "id è obbligatorio"},
}

NEWSLETTER_ID_OPTIONAL_QUERY_SCHEMA = {
    "id": {"required": False, "types": str},
}


def _validate_participants(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(entry, dict) for entry in value)


NEWSLETTER_SIGNUP_SCHEMA = {
    "email": {
        "required": True,
        "types": str,
        "error": "Email obbligatoria per l'iscrizione",
    }
}

NEWSLETTER_PARTICIPANTS_SCHEMA = {
    "participants": {
        "required": True,
        "validator": _validate_participants,
        "error": "participants deve essere un array non vuoto di oggetti",
    }
}
