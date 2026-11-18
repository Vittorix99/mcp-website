"""Received participant payments outside the website, without purchase duplication."""
from decimal import Decimal, InvalidOperation

_MANUAL_METHODS = {'cash', 'iban', 'private_paypal'}


def manual_received_total(participants) -> float:
    total = Decimal('0.00')
    for participant in participants:
        link = getattr(participant, 'purchase_id', None)
        if link is not None and link != '':
            continue
        method = getattr(participant, 'payment_method', None)
        method = getattr(method, 'value', method)
        if not isinstance(method, str) or method not in _MANUAL_METHODS:
            continue
        try:
            amount = Decimal(str(getattr(participant, 'price', None)))
            if not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal('.01')):
                continue
            total += amount
        except InvalidOperation:
            continue
    return float(total)
