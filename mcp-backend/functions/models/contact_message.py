from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class ContactMessage(FirestoreModel):
    """Represents messages stored inside ``contact_message``."""

    name: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    subject: Optional[str] = None
    answered: bool = False
    participant_id: Optional[str] = field(default=None, metadata={"firestore_name": "participant_id"})
    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "event_id"})
    error_message: Optional[str] = None
    timestamp: Optional[Any] = None
