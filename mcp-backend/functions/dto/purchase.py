from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from models import Purchase


@dataclass
class PurchaseDTO:
    payer_name: Optional[str] = None
    payer_surname: Optional[str] = None
    slug: Optional[str] = None
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
    payment_method: Optional[str] = None
    capture_status: Optional[str] = None
    fields_present: Optional[Set[str]] = field(default=None, repr=False)

    @classmethod
    def from_model(cls, purchase: Purchase) -> "PurchaseDTO":
        return cls(
            payer_name=purchase.payer_name,
            payer_surname=purchase.payer_surname,
            slug=purchase.slug,
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
            payment_method=purchase.payment_method,
            capture_status=purchase.capture_status,
        )

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PurchaseDTO":
        dto = cls(
            payer_name=payload.get("payer_name"),
            payer_surname=payload.get("payer_surname"),
            slug=payload.get("slug"),
            payer_email=payload.get("payer_email"),
            amount_total=payload.get("amount_total"),
            currency=payload.get("currency"),
            paypal_fee=payload.get("paypal_fee"),
            net_amount=payload.get("net_amount"),
            transaction_id=payload.get("transaction_id"),
            order_id=payload.get("order_id"),
            status=payload.get("status"),
            timestamp=payload.get("timestamp"),
            type=payload.get("type"),
            ref_id=payload.get("ref_id"),
            payment_method=payload.get("payment_method"),
            capture_status=payload.get("capture_status"),
        )
        dto.fields_present = set(payload.keys())
        return dto

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "payer_name": self.payer_name,
            "payer_surname": self.payer_surname,
            "slug": self.slug,
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
            "payment_method": self.payment_method,
            "capture_status": self.capture_status,
        }
        return {k: v for k, v in payload.items() if v is not None}

    def validate(self, *, is_update: bool = False) -> Optional[str]:
        if is_update:
            return None
        required_fields = [
            "payer_name",
            "payer_surname",
            "payer_email",
            "amount_total",
            "currency",
            "transaction_id",
            "order_id",
            "timestamp",
            "type",
        ]
        missing = [field for field in required_fields if not getattr(self, field, None)]
        if missing:
            return f"Missing fields: {', '.join(missing)}"
        return None
