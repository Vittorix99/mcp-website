from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from models import ContactMessage


@dataclass
class ContactMessageDTO:
    """DTO for contact messages between frontend and backend."""

    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    subject: Optional[str] = None
    answered: bool = False
    participant_id: Optional[str] = None
    event_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[Any] = None

    @classmethod
    def from_model(cls, message: ContactMessage) -> "ContactMessageDTO":
        return cls(
            id=message.id,
            name=message.name,
            email=message.email,
            message=message.message,
            subject=message.subject,
            answered=message.answered,
            participant_id=message.participant_id,
            event_id=message.event_id,
            error_message=message.error_message,
            timestamp=message.timestamp,
        )

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ContactMessageDTO":
        def pick(key, alternate=None):
            if key in payload:
                return payload.get(key)
            if alternate and alternate in payload:
                return payload.get(alternate)
            return None

        return cls(
            id=payload.get("id"),
            name=pick("name"),
            email=pick("email"),
            message=pick("message"),
            subject=pick("subject"),
            answered=bool(payload.get("answered")) if "answered" in payload else False,
            participant_id=pick("participant_id", "participantId"),
            event_id=pick("event_id", "eventId"),
            error_message=pick("error_message", "errorMessage"),
            timestamp=pick("timestamp"),
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "message": self.message,
            "subject": self.subject,
            "answered": self.answered,
            "participant_id": self.participant_id,
            "event_id": self.event_id,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }
        return {k: v for k, v in payload.items() if v is not None}
