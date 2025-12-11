"\"\"\"Validation schemas for admin purchase endpoints.\"\"\""

CREATE_PURCHASE_SCHEMA = {
    "payer_name": {"required": True, "types": str},
    "payer_surname": {"required": True, "types": str},
    "payer_email": {"required": True, "types": str},
    "amount_total": {"required": True, "types": str},
    "currency": {"required": True, "types": str},
    "transaction_id": {"required": True, "types": str},
    "order_id": {"required": True, "types": str},
    "timestamp": {"required": True, "types": (str, int)},
    "type": {"required": True, "types": str},
    "status": {"required": False, "types": str},
    "paypal_fee": {"required": False, "types": str},
    "net_amount": {"required": False, "types": str},
    "ref_id": {"required": False, "types": str},
}

DELETE_PURCHASE_SCHEMA = {
    "purchase_id": {"required": True, "types": str},
}

PURCHASE_ID_QUERY_SCHEMA = {
    "id": {"required": True, "types": str},
}
