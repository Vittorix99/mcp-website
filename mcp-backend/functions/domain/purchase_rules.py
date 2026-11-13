"""Eligibility of confirmed online purchases for financial statistics."""
from models.enums import PurchaseStatus


def is_completed_purchase(purchase) -> bool:
    for field in ('status', 'capture_status'):
        value = getattr(purchase, field, None)
        value = getattr(value, 'value', value)
        if not isinstance(value, str) or value.upper() != PurchaseStatus.COMPLETED.value:
            return False
    return True
