"""Validation helpers for the event payment endpoints."""

from typing import Any, Dict


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_participants(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(entry, dict) for entry in value)


ValidationRule = Dict[str, Any]


def _validate_against_schema(payload: Any, schema: Dict[str, ValidationRule]) -> bool:
    if not isinstance(payload, dict):
        return False

    for field_name, rule in schema.items():
        required = rule.get("required", True)
        value = payload.get(field_name)

        if required and value in (None, ""):
            return False

        expected_type = rule.get("types")
        if value not in (None, "") and expected_type:
            types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
            if not isinstance(value, types):
                return False

        validator = rule.get("validator")
        if validator and value not in (None, "") and not validator(value):
            return False

    return True


CART_ITEM_SCHEMA = {
    "eventId": {"required": True, "validator": _is_non_empty_str},
    "participants": {"required": True, "validator": _validate_participants},
    "membershipFee": {"required": False, "types": (int, float, str)},
    "eventMeta": {"required": False, "types": dict},
}


def _validate_cart(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 1:
        return False

    return _validate_against_schema(value[0], CART_ITEM_SCHEMA)


PREORDER_SCHEMA = {
    "cart": {
        "required": True,
        "validator": _validate_cart,
        "error": "The cart must include exactly one valid item with an eventId and participants",
    }
}


CAPTURE_ORDER_SCHEMA = {
    "order_id": {
        "required": True,
        "types": str,
        "error": "Missing order_id for capture",
    }
}
