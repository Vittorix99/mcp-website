"""Field validation schemas for membership-related endpoints."""

UPDATE_MEMBERSHIP_SCHEMA = {
    "membership_id": {
        "required": True,
        "types": str,
        "error": "membership_id è obbligatorio",
    },
    "name": {"required": False, "types": str},
    "surname": {"required": False, "types": str},
    "email": {"required": False, "types": str},
    "phone": {"required": False, "types": str},
    "birthdate": {"required": False, "types": str},
}

CREATE_MEMBERSHIP_SCHEMA = {
    "name": {"required": False, "types": str},
    "surname": {"required": False, "types": str},
    "email": {"required": False, "types": str},
    "phone": {"required": False, "types": str},
    "birthdate": {"required": True, "types": str},
    "send_card_on_create": {"required": False, "types": bool},
}

DELETE_MEMBERSHIP_SCHEMA = {
    "membership_id": {"required": True, "types": str, "error": "membership_id è obbligatorio"},
}

SEND_CARD_SCHEMA = {
    "membership_id": {"required": True, "types": str, "error": "membership_id è obbligatorio"},
}

SET_PRICE_SCHEMA = {
    "membership_fee": {
        "required": True,
        "types": (int, float),
        "error": "membership_fee deve essere un numero",
    },
}

MEMBERSHIP_ID_QUERY_SCHEMA = {
    "id": {"required": True, "types": str, "error": "membership_id è obbligatorio"},
}
