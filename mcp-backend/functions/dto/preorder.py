from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


@dataclass
class CheckoutParticipantDTO:
    name: str = ""
    surname: str = ""
    email: str = ""
    phone: str = ""
    birthdate: Optional[str] = None
    newsletter_consent: bool = False
    gender: Optional[str] = None
    gender_probability: Optional[float] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "CheckoutParticipantDTO":
        gender_probability = payload.get("gender_probability")
        if gender_probability is None:
            gender_probability = payload.get("genderProbability")
        return cls(
            name=_clean_str(payload.get("name")),
            surname=_clean_str(payload.get("surname")),
            email=_clean_str(payload.get("email")),
            phone=_clean_str(payload.get("phone")),
            birthdate=payload.get("birthdate") or None,
            newsletter_consent=bool(payload.get("newsletterConsent", False)),
            gender=payload.get("gender"),
            gender_probability=gender_probability,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "phone": self.phone,
            "birthdate": self.birthdate,
            "newsletterConsent": self.newsletter_consent,
            "gender": self.gender,
            "gender_probability": self.gender_probability,
        }
        return {k: v for k, v in payload.items() if v not in (None, "")}


def _build_participants(value: Any) -> List[CheckoutParticipantDTO]:
    if isinstance(value, list):
        participants: List[CheckoutParticipantDTO] = []
        for entry in value:
            if isinstance(entry, dict):
                participants.append(CheckoutParticipantDTO.from_payload(entry))
        return participants
    return []


@dataclass
class PreOrderCartItemDTO:
    eventId: str
    participants: List[CheckoutParticipantDTO] = field(default_factory=list)
    eventMeta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PreOrderCartItemDTO":
        return cls(
            eventId=payload.get("eventId", ""),
            participants=_build_participants(payload.get("participants")),
            eventMeta=payload.get("eventMeta") or {},
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "eventId": self.eventId,
            "participants": [participant.to_payload() for participant in self.participants],
            "eventMeta": self.eventMeta,
        }
        return {k: v for k, v in payload.items() if v not in ({}, None) or k == "participants"}


@dataclass
class PreOrderDTO:
    cart: List[PreOrderCartItemDTO] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PreOrderDTO":
        raw_cart = payload.get("cart") or []
        cart_items: List[PreOrderCartItemDTO] = []
        for entry in raw_cart:
            if isinstance(entry, dict):
                cart_items.append(PreOrderCartItemDTO.from_payload(entry))
        return cls(cart=cart_items)

    def to_payload(self) -> Dict[str, Any]:
        return {"cart": [item.to_payload() for item in self.cart]}


@dataclass
class OrderCaptureDTO:
    order_id: str

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "OrderCaptureDTO":
        return cls(order_id=payload.get("order_id", ""))

    def to_payload(self) -> Dict[str, Any]:
        return {"order_id": self.order_id}
