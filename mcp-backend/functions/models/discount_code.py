from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel
from .enums import DiscountType


@dataclass
class DiscountCode(FirestoreModel):
    """Discount code scoped to a single event."""

    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "event_id"})
    code: Optional[str] = field(default=None, metadata={"firestore_name": "code"})
    discount_type: Optional[DiscountType] = field(
        default=None,
        metadata={"firestore_name": "discountType", "enum": DiscountType},
    )
    discount_value: Optional[float] = field(default=None, metadata={"firestore_name": "discountValue"})
    max_uses: Optional[int] = field(default=None, metadata={"firestore_name": "maxUses"})
    used_count: int = field(default=0, metadata={"firestore_name": "usedCount"})
    is_active: bool = field(default=True, metadata={"firestore_name": "isActive"})
    restricted_membership_id: Optional[str] = field(
        default=None,
        metadata={"firestore_name": "restrictedMembershipId"},
    )
    restricted_email: Optional[str] = field(default=None, metadata={"firestore_name": "restrictedEmail"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})
    created_by: Optional[str] = field(default=None, metadata={"firestore_name": "createdBy"})
    updated_at: Optional[Any] = field(default=None, metadata={"firestore_name": "updatedAt"})
    updated_by: Optional[str] = field(default=None, metadata={"firestore_name": "updatedBy"})
