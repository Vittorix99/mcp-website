"""Eligibility of confirmed online purchases for financial statistics."""
from models.enums import PurchaseStatus, PurchaseTypes


def is_completed_purchase(purchase) -> bool:
    for field in ('status', 'capture_status'):
        value = getattr(purchase, field, None)
        value = getattr(value, 'value', value)
        if not isinstance(value, str) or value.upper() != PurchaseStatus.COMPLETED.value:
            return False
    return True


def is_completed_event_purchase(purchase) -> bool:
    kind = getattr(purchase, 'purchase_type', None)
    kind = getattr(kind, 'value', kind)
    if str(kind or '').lower() not in {PurchaseTypes.EVENT.value, 'event_and_membership'}:
        return False
    if not getattr(purchase, 'ref_id', None):
        return False
    try:
        count = int(getattr(purchase, 'participants_count', 0) or 0)
    except (TypeError, ValueError, OverflowError):
        return False
    return count > 0 and is_completed_purchase(purchase)
