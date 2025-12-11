from dataclasses import dataclass, field
from typing import Optional

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
