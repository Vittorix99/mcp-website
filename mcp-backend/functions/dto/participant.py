from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from models import EventParticipant


@dataclass
class EventParticipantDTO:
    """DTO used when sending participant data between frontend and backend."""

    id: Optional[str] = None
    event_id: str = ""
    name: str = ""
    surname: str = ""
    email: str = ""
    phone: str = ""
    birthdate: Optional[str] = None
    membership_id: Optional[str] = None
    membership_included: bool = False
    ticket_pdf_url: Optional[str] = None
    ticket_sent: bool = False
    send_ticket_on_create: bool = True
    location_sent: bool = False
    location_sent_at: Optional[Any] = None
    location_job_id: Optional[str] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = None
    newsletter_consent: bool = False
    price: Optional[float] = None
    purchase_id: Optional[str] = None
    created_at: Optional[Any] = None

    @classmethod
    def from_model(cls, participant: EventParticipant) -> "EventParticipantDTO":
        return cls(
            id=participant.id,
            event_id=participant.event_id,
            name=participant.name,
            surname=participant.surname,
            email=participant.email,
            phone=participant.phone,
            birthdate=participant.birthdate,
            membership_id=participant.membership_id,
            membership_included=participant.membership_included,
            ticket_pdf_url=participant.ticket_pdf_url,
            ticket_sent=participant.ticket_sent,
            send_ticket_on_create=participant.send_ticket_on_create,
            location_sent=participant.location_sent,
            location_sent_at=participant.location_sent_at,
            location_job_id=participant.location_job_id,
            gender=participant.gender,
            gender_probability=participant.gender_probability,
            newsletter_consent=participant.newsletter_consent,
            price=participant.price,
            purchase_id=participant.purchase_id,
            created_at=participant.created_at,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "event_id": self.event_id,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "phone": self.phone,
            "birthdate": self.birthdate,
            "membershipId": self.membership_id,
            "membership_included": self.membership_included,
            "ticket_pdf_url": self.ticket_pdf_url,
            "ticket_sent": self.ticket_sent,
            "send_ticket_on_create": self.send_ticket_on_create,
            "location_sent": self.location_sent,
            "location_sent_at": self.location_sent_at,
            "location_job_id": self.location_job_id,
            "gender": self.gender,
            "gender_probability": self.gender_probability,
            "newsletterConsent": self.newsletter_consent,
            "price": self.price,
            "purchase_id": self.purchase_id,
            "createdAt": self.created_at,
        }
        return {k: v for k, v in payload.items() if v is not None}
