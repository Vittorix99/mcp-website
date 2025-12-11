from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from models import Purchase


@dataclass
class PurchaseDTO:
    payer_name: Optional[str] = None
    payer_surname: Optional[str] = None
    payer_email: Optional[str] = None
    amount_total: Optional[str] = None
    currency: Optional[str] = None
    paypal_fee: Optional[str] = None
    net_amount: Optional[str] = None
    transaction_id: Optional[str] = None
    order_id: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[Any] = None
    type: Optional[str] = None
    ref_id: Optional[str] = None

    @classmethod
    def from_model(cls, purchase: Purchase) -> "PurchaseDTO":
        return cls(
            payer_name=purchase.payer_name,
            payer_surname=purchase.payer_surname,
            payer_email=purchase.payer_email,
            amount_total=purchase.amount_total,
            currency=purchase.currency,
            paypal_fee=purchase.paypal_fee,
            net_amount=purchase.net_amount,
            transaction_id=purchase.transaction_id,
            order_id=purchase.order_id,
            status=purchase.status,
            timestamp=purchase.timestamp,
            type=purchase.purchase_type.value if purchase.purchase_type else None,
            ref_id=purchase.ref_id,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "payer_name": self.payer_name,
            "payer_surname": self.payer_surname,
            "payer_email": self.payer_email,
            "amount_total": self.amount_total,
            "currency": self.currency,
            "paypal_fee": self.paypal_fee,
            "net_amount": self.net_amount,
            "transaction_id": self.transaction_id,
            "order_id": self.order_id,
            "status": self.status,
            "timestamp": self.timestamp,
            "type": self.type,
            "ref_id": self.ref_id,
        }
        return {k: v for k, v in payload.items() if v is not None}
