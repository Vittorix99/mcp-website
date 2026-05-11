from dataclasses import dataclass, field
from typing import List, Optional

from .enums import EventPurchaseAccessType, PurchaseTypes
from .purchase import Purchase


@dataclass
class EventPurchase(Purchase):
    """
    Represents a purchase linked to an event. The purchase_type is always
    ``EVENT`` in the current platform scope.
    """

    purchase_type: PurchaseTypes = field(
        default=PurchaseTypes.EVENT,
        init=False,
        metadata={"firestore_name": "type", "enum": PurchaseTypes},
    )
    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "event_id"})
    event_purchase_type: EventPurchaseAccessType = field(
        default=EventPurchaseAccessType.PUBLIC,
        metadata={"firestore_name": "eventPurchaseType", "enum": EventPurchaseAccessType},
    )
    participants_count: int = field(default=0, metadata={"firestore_name": "participants_count"})
    membership_ids: List[str] = field(default_factory=list, metadata={"firestore_name": "membership_ids"})
    discount_code_id: Optional[str] = field(default=None, metadata={"firestore_name": "discountCodeId"})
    discount_code: Optional[str] = field(default=None, metadata={"firestore_name": "discountCode"})
    discount_amount: Optional[float] = field(default=None, metadata={"firestore_name": "discountAmount"})
