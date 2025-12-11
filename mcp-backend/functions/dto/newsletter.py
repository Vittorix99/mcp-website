from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models import NewsletterConsent, NewsletterSignup


@dataclass
class NewsletterSignupDTO:
    id: Optional[str] = None
    email: str = ""
    timestamp: Optional[Any] = None
    active: bool = True
    source: Optional[str] = None

    @classmethod
    def from_model(cls, signup: NewsletterSignup) -> "NewsletterSignupDTO":
        return cls(
            id=signup.id,
            email=signup.email,
            timestamp=signup.timestamp,
            active=signup.active,
            source=signup.source,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "email": self.email,
            "timestamp": self.timestamp,
            "active": self.active,
            "source": self.source,
        }
        return {k: v for k, v in payload.items() if v is not None}

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "NewsletterSignupDTO":
        return cls(
            email=str(payload.get("email", "")).strip(),
            source=payload.get("source"),
            active=payload.get("active", True),
        )


@dataclass
class NewsletterConsentDTO:
    id: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = None
    event_id: Optional[str] = None
    participant_id: Optional[str] = None
    timestamp: Optional[Any] = None
    source: str = "participant_event"

    @classmethod
    def from_model(cls, consent: NewsletterConsent) -> "NewsletterConsentDTO":
        return cls(
            id=consent.id,
            name=consent.name,
            surname=consent.surname,
            email=consent.email,
            phone=consent.phone,
            birthdate=consent.birthdate,
            gender=consent.gender,
            gender_probability=consent.gender_probability,
            event_id=consent.event_id,
            participant_id=consent.participant_id,
            timestamp=consent.timestamp,
            source=consent.source,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "phone": self.phone,
            "birthdate": self.birthdate,
            "gender": self.gender,
            "gender_probability": self.gender_probability,
            "event_id": self.event_id,
            "participant_id": self.participant_id,
            "timestamp": self.timestamp,
            "source": self.source,
        }
        return {k: v for k, v in payload.items() if v is not None}


@dataclass
class NewsletterParticipantsDTO:
    participants: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "NewsletterParticipantsDTO":
        raw = payload.get("participants") or []
        normalized = [entry for entry in raw if isinstance(entry, dict)]
        return cls(participants=normalized)

    def to_payload(self) -> Dict[str, Any]:
        return {"participants": self.participants}
