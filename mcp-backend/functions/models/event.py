from dataclasses import dataclass, field
from typing import Any, List, Optional

from .base import FirestoreModel
from .enums import EventPurchaseAccessType


@dataclass
class Event(FirestoreModel):
    """Represents an event document stored in the ``events`` collection."""

    title: str = ""
    description: str = ""
    date: str = ""
    start_time: Optional[str] = field(default=None, metadata={"firestore_name": "startTime"})
    end_time: Optional[str] = field(default=None, metadata={"firestore_name": "endTime"})
    location: Optional[str] = None
    location_hint: Optional[str] = field(default=None, metadata={"firestore_name": "locationHint"})
    price: Optional[float] = None
    fee: Optional[float] = None
    max_participants: Optional[int] = field(default=None, metadata={"firestore_name": "maxParticipants"})
    active: bool = True
    image: Optional[str] = None
    lineup: List[str] = field(default_factory=list)
    note: str = ""
    photo_path: Optional[str] = field(default=None, metadata={"firestore_name": "photoPath"})
    purchase_mode: EventPurchaseAccessType = field(
        default=EventPurchaseAccessType.PUBLIC,
        metadata={"firestore_name": "type", "enum": EventPurchaseAccessType},
    )
    allow_duplicates: bool = field(default=False, metadata={"firestore_name": "allowDuplicates"})
    over21_only: bool = field(default=False, metadata={"firestore_name": "over21Only"})
    only_females: bool = field(default=False, metadata={"firestore_name": "onlyFemales"})
    participants_count: int = field(default=0, metadata={"firestore_name": "participantsCount"})
    external_link: Optional[str] = field(default=None, metadata={"firestore_name": "externalLink"})
    membership_fee: Optional[float] = field(default=None, metadata={"firestore_name": "membershipFee"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})
    created_by: Optional[str] = field(default=None, metadata={"firestore_name": "createdBy"})
    updated_at: Optional[Any] = field(default=None, metadata={"firestore_name": "updatedAt"})
    updated_by: Optional[str] = field(default=None, metadata={"firestore_name": "updatedBy"})
