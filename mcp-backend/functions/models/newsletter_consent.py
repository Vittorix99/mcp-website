from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class NewsletterConsent(FirestoreModel):
    """Represents a row inside ``newsletter_consents``."""

    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = None
    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "event_id"})
    participant_id: Optional[str] = field(default=None, metadata={"firestore_name": "participant_id"})
    timestamp: Optional[Any] = None
    source: str = field(default="participant_event")
