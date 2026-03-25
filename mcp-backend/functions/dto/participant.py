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
    membership_included: Optional[bool] = None
    entered: Optional[bool] = None
    entered_at: Optional[Any] = None
    ticket_pdf_url: Optional[str] = None
    ticket_sent: Optional[bool] = None
    send_ticket_on_create: Optional[bool] = None
    location_sent: Optional[bool] = None
    location_sent_at: Optional[Any] = None
    location_job_id: Optional[str] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = None
    newsletter_consent: Optional[bool] = None
    price: Optional[float] = None
    payment_method: Optional[str] = None
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
            entered=participant.entered,
            entered_at=participant.entered_at,
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
            payment_method=participant.payment_method.value if participant.payment_method else None,
            purchase_id=participant.purchase_id,
            created_at=participant.created_at,
        )

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "EventParticipantDTO":
        def pick(key, alternate=None):
            if key in payload:
                return payload.get(key)
            if alternate and alternate in payload:
                return payload.get(alternate)
            return None

        def pick_bool(key, alternate=None):
            if key in payload:
                value = payload.get(key)
                return None if value is None else bool(value)
            if alternate and alternate in payload:
                value = payload.get(alternate)
                return None if value is None else bool(value)
            return None

        return cls(
            id=payload.get("id"),
            event_id=pick("event_id", "eventId") or "",
            name=pick("name") or "",
            surname=pick("surname") or "",
            email=pick("email") or "",
            phone=pick("phone") or "",
            birthdate=pick("birthdate"),
            membership_id=pick("membership_id", "membershipId"),
            membership_included=pick_bool("membership_included", "membershipIncluded"),
            entered=pick_bool("entered"),
            entered_at=pick("entered_at", "enteredAt"),
            ticket_pdf_url=pick("ticket_pdf_url"),
            ticket_sent=pick_bool("ticket_sent"),
            send_ticket_on_create=pick_bool("send_ticket_on_create", "sendTicketOnCreate"),
            location_sent=pick_bool("location_sent"),
            location_sent_at=pick("location_sent_at"),
            location_job_id=pick("location_job_id"),
            gender=pick("gender"),
            gender_probability=pick("gender_probability"),
            newsletter_consent=pick_bool("newsletterConsent", "newsletter_consent"),
            price=pick("price"),
            payment_method=pick("payment_method"),
            purchase_id=pick("purchase_id"),
            created_at=pick("createdAt", "created_at"),
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
            "entered": self.entered,
            "entered_at": self.entered_at,
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
            "payment_method": self.payment_method,
            "purchase_id": self.purchase_id,
            "createdAt": self.created_at,
        }
        return {k: v for k, v in payload.items() if v is not None}

    def to_update_payload(self) -> Dict[str, Any]:
        payload = self.to_payload()
        payload.pop("id", None)
        payload.pop("event_id", None)
        return {k: v for k, v in payload.items() if not (isinstance(v, str) and v == "")}
