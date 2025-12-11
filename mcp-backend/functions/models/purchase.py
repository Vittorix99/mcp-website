from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import PurchaseTypes
from .base import FirestoreModel


@dataclass
class Purchase(FirestoreModel):
    """Base class representing a completed payment stored in ``purchases``."""

    payer_name: str = field(default="", metadata={"firestore_name": "payer_name"})
    payer_surname: str = field(default="", metadata={"firestore_name": "payer_surname"})
    payer_email: str = field(default="", metadata={"firestore_name": "payer_email"})
    amount_total: str = field(default="", metadata={"firestore_name": "amount_total"})
    currency: str = ""
    paypal_fee: Optional[str] = field(default=None, metadata={"firestore_name": "paypal_fee"})
    net_amount: Optional[str] = field(default=None, metadata={"firestore_name": "net_amount"})
    transaction_id: str = field(default="", metadata={"firestore_name": "transaction_id"})
    order_id: str = field(default="", metadata={"firestore_name": "order_id"})
    status: str = ""
    timestamp: Optional[Any] = None
    purchase_type: PurchaseTypes = field(
        default=PurchaseTypes.EVENT, metadata={"firestore_name": "type", "enum": PurchaseTypes}
    )
    ref_id: Optional[str] = field(default=None, metadata={"firestore_name": "ref_id"})
    payment_method: Optional[str] = field(default=None, metadata={"firestore_name": "payment_method"})
    capture_status: Optional[str] = field(default=None, metadata={"firestore_name": "capture_status"})
