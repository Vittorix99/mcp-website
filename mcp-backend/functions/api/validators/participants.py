"""Validation rules for admin participant endpoints."""

from typing import Any

GET_PARTICIPANTS_BY_EVENT_SCHEMA = {
    "eventId": {"required": True, "types": str},
}

GET_PARTICIPANT_SCHEMA = {
    "participantId": {"required": True, "types": str},
}

CREATE_PARTICIPANT_SCHEMA = {
    "event_id": {"required": True, "types": str},
    "name": {"required": False, "types": str},
    "surname": {"required": False, "types": str},
    "email": {"required": False, "types": str},
    "phone": {"required": False, "types": str},
    "birthdate": {"required": False, "types": str},
    "membership_included": {"required": False, "types": bool},
}

UPDATE_PARTICIPANT_SCHEMA = {
    "event_id": {"required": True, "types": str},
    "participantId": {"required": True, "types": str},
    "name": {"required": False, "types": str},
    "surname": {"required": False, "types": str},
    "email": {"required": False, "types": str},
    "phone": {"required": False, "types": str},
    "birthdate": {"required": False, "types": str},
    "membership_included": {"required": False, "types": bool},
}

DELETE_PARTICIPANT_SCHEMA = {
    "event_id": {"required": True, "types": str},
    "participantId": {"required": True, "types": str},
}

SEND_TICKET_SCHEMA = {
    "eventId": {"required": True, "types": str},
    "participantId": {"required": True, "types": str},
}

SEND_LOCATION_SCHEMA = {
    "eventId": {"required": True, "types": str},
    "participantId": {"required": True, "types": str},
    "address": {"required": False, "types": str},
    "link": {"required": False, "types": str},
    "message": {"required": False, "types": str},
}

SEND_LOCATION_TO_ALL_SCHEMA = {
    "eventId": {"required": True, "types": str},
    "address": {"required": False, "types": str},
    "link": {"required": False, "types": str},
    "message": {"required": False, "types": str},
}


def _validate_participants_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(entry, dict) for entry in value)


CHECK_PARTICIPANTS_SCHEMA = {
    "eventId": {"required": True, "types": str},
    "participants": {"required": True, "validator": _validate_participants_list},
}
