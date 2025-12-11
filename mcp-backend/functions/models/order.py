from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .enums import EventPurchaseAccessType, PurchaseTypes
from .base import FirestoreModel


@dataclass
class Order(FirestoreModel):
    """Represents a temporary order stored in ``orders`` before capture."""

    order_id: Optional[str] = field(default=None, metadata={"firestore_name": "orderId"})
    order_status: str = field(default="CREATED", metadata={"firestore_name": "orderStatus"})
    purchase_type: PurchaseTypes = field(
        default=PurchaseTypes.EVENT, metadata={"firestore_name": "purchase_type", "enum": PurchaseTypes}
    )
    cart: List[Dict[str, Any]] = field(default_factory=list)
    total: float = 0.0
    reference_id: Optional[str] = field(default=None, metadata={"firestore_name": "reference_id"})
    event_meta: Dict[str, Any] = field(default_factory=dict, metadata={"firestore_name": "eventMeta"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})


@dataclass
class EventOrder(Order):
    """Order specialization for event purchases (single cart item)."""

    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "eventId"})
    participants: List[Dict[str, Any]] = field(default_factory=list)
    event_price: float = field(default=0.0, metadata={"firestore_name": "eventPrice"})
    event_fee: float = field(default=0.0, metadata={"firestore_name": "eventFee"})
    membership_targets: List[Dict[str, Any]] = field(default_factory=list, metadata={"firestore_name": "membershipTargets"})
    membership_fee: Optional[float] = field(default=None, metadata={"firestore_name": "membershipFee"})
    purchase_mode: EventPurchaseAccessType = field(
        default=EventPurchaseAccessType.PUBLIC,
        metadata={"firestore_name": "purchaseMode", "enum": EventPurchaseAccessType},
    )
    membership_lookup: Dict[str, Dict[str, Any]] = field(
        default_factory=dict, metadata={"firestore_name": "membershipLookup"}
    )
    event_meta: Dict[str, Any] = field(default_factory=dict, metadata={"firestore_name": "eventMeta"})

