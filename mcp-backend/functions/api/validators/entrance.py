GENERATE_SCAN_TOKEN_SCHEMA = {
    "event_id": {
        "required": True,
        "types": str,
        "error": "event_id is required and must be a string",
    },
}

VALIDATE_ENTRY_SCHEMA = {
    "membership_id": {
        "required": True,
        "types": str,
        "error": "membership_id is required and must be a string",
    },
    "scan_token": {
        "required": True,
        "types": str,
        "error": "scan_token is required and must be a string",
    },
}

VERIFY_SCAN_TOKEN_SCHEMA = {
    "token": {
        "required": True,
        "types": str,
        "error": "token is required and must be a string",
    },
}

DEACTIVATE_SCAN_TOKEN_SCHEMA = {
    "token": {
        "required": True,
        "types": str,
        "error": "token is required and must be a string",
    },
}
