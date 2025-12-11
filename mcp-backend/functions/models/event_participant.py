from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class EventParticipant(FirestoreModel):
    """Represents a participant within ``participants/{eventId}/participants_event``."""

    event_id: str = field(default="", metadata={"firestore_name": "event_id"})
    name: str = ""
    surname: str = ""
    email: str = ""
    phone: str = ""
    birthdate: Optional[str] = None
    membership_id: Optional[str] = field(default=None, metadata={"firestore_name": "membershipId"})
    membership_included: bool = field(default=False, metadata={"firestore_name": "membership_included"})
    ticket_pdf_url: Optional[str] = None
    ticket_sent: bool = False
    send_ticket_on_create: bool = field(default=True, metadata={"firestore_name": "send_ticket_on_create"})
    location_sent: bool = False
    location_sent_at: Optional[Any] = None
    location_job_id: Optional[str] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = None
    newsletter_consent: bool = field(default=False, metadata={"firestore_name": "newsletterConsent"})
    price: Optional[float] = None
    purchase_id: Optional[str] = field(default=None, metadata={"firestore_name": "purchase_id"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})
