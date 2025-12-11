"\"\"\"Validation schemas for admin settings API.\"\"\""

GET_SETTING_SCHEMA = {
    "key": {"required": False, "types": str},
}

SET_SETTING_SCHEMA = {
    "key": {"required": True, "types": str},
    "value": {"required": True},
}
