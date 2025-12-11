from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models import Event


@dataclass
class EventDTO:
    """Data Transfer Object for exposing an event payload."""

    id: Optional[str] = None
    title: str = ""
    description: str = ""
    date: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location_hint: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = None
    fee: Optional[float] = None
    max_participants: Optional[int] = None
    active: bool = True
    image: Optional[str] = None
    lineup: List[str] = field(default_factory=list)
    note: str = ""
    photo_path: Optional[str] = None
    purchase_mode: Optional[str] = None
    allow_duplicates: bool = False
    over21_only: bool = False
    only_females: bool = False
    participants_count: int = 0
    external_link: Optional[str] = None
    membership_fee: Optional[float] = None
    created_at: Optional[Any] = None
    created_by: Optional[str] = None
    updated_at: Optional[Any] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_model(cls, event: Event) -> "EventDTO":
        dto = cls(
            id=event.id,
            title=event.title,
            description=event.description,
            date=event.date,
            start_time=event.start_time,
            end_time=event.end_time,
            location_hint=event.location_hint,
            location=event.location,
            price=event.price,
            fee=event.fee,
            max_participants=event.max_participants,
            active=event.active,
            image=event.image,
            lineup=event.lineup or [],
            note=event.note,
            photo_path=event.photo_path,
            purchase_mode=event.purchase_mode.value if event.purchase_mode else None,
            allow_duplicates=event.allow_duplicates,
            over21_only=event.over21_only,
            only_females=event.only_females,
            participants_count=event.participants_count,
            external_link=event.external_link,
            membership_fee=event.membership_fee,
            created_at=event.created_at,
            created_by=event.created_by,
            updated_at=event.updated_at,
            updated_by=event.updated_by,
        )
        return dto

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "locationHint": self.location_hint,
            "location": self.location,
            "price": self.price,
            "fee": self.fee,
            "maxParticipants": self.max_participants,
            "active": self.active,
            "image": self.image,
            "lineup": self.lineup,
            "note": self.note,
            "photoPath": self.photo_path,
            "purchaseMode": self.purchase_mode,
            "allowDuplicates": self.allow_duplicates,
            "over21Only": self.over21_only,
            "onlyFemales": self.only_females,
            "participantsCount": self.participants_count,
            "externalLink": self.external_link,
            "membershipFee": self.membership_fee,
            "createdAt": self.created_at,
            "createdBy": self.created_by,
            "updatedAt": self.updated_at,
            "updatedBy": self.updated_by,
        }
        return {k: v for k, v in payload.items() if v is not None}

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "EventDTO":
        return cls(
            id=payload.get("id"),
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            date=payload.get("date", ""),
            start_time=payload.get("startTime") or payload.get("start_time"),
            end_time=payload.get("endTime") or payload.get("end_time"),
            location_hint=payload.get("locationHint") or payload.get("location_hint"),
            location=payload.get("location"),
            price=payload.get("price"),
            fee=payload.get("fee"),
            max_participants=payload.get("maxParticipants") or payload.get("max_participants"),
            active=payload.get("active", True),
            image=payload.get("image"),
            lineup=payload.get("lineup") or [],
            note=payload.get("note", ""),
            photo_path=payload.get("photoPath") or payload.get("photo_path"),
            purchase_mode=payload.get("purchaseMode") or payload.get("purchase_mode"),
            allow_duplicates=payload.get("allowDuplicates") if "allowDuplicates" in payload else payload.get("allow_duplicates", False),
            over21_only=payload.get("over21Only") if "over21Only" in payload else payload.get("over21_only", False),
            only_females=payload.get("onlyFemales") if "onlyFemales" in payload else payload.get("only_females", False),
            participants_count=payload.get("participantsCount") or payload.get("participants_count", 0),
            external_link=payload.get("externalLink") or payload.get("external_link"),
            membership_fee=payload.get("membershipFee") or payload.get("membership_fee"),
            created_at=payload.get("createdAt") or payload.get("created_at"),
            created_by=payload.get("createdBy") or payload.get("created_by"),
            updated_at=payload.get("updatedAt") or payload.get("updated_at"),
            updated_by=payload.get("updatedBy") or payload.get("updated_by"),
        )
