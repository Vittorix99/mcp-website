from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from models import Event


@dataclass
class EventDTO:
    """Data Transfer Object for exposing an event payload."""

    id: Optional[str] = None
    title: str = ""
    slug: Optional[str] = None
    date: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location_hint: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = None
    fee: Optional[float] = None
    max_participants: Optional[int] = None
    status: str = "active"
    image: Optional[str] = None
    lineup: Optional[List[str]] = None
    note: str = ""
    photo_path: Optional[str] = None
    purchase_mode: Optional[str] = None
    allow_duplicates: bool = False
    over21_only: bool = False
    only_females: bool = False
    participants_count: int = 0
    external_link: Optional[str] = None
    created_at: Optional[Any] = None
    created_by: Optional[str] = None
    updated_at: Optional[Any] = None
    updated_by: Optional[str] = None
    fields_present: Optional[Set[str]] = field(default=None, repr=False)

    @classmethod
    def from_model(cls, event: Event) -> "EventDTO":
        dto = cls(
            id=event.id,
            title=event.title,
            slug=event.slug,
            date=event.date,
            start_time=event.start_time,
            end_time=event.end_time,
            location_hint=event.location_hint,
            location=event.location,
            price=event.price,
            fee=event.fee,
            max_participants=event.max_participants,
            status=event.status.value if event.status else "active",
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
            created_at=event.created_at,
            created_by=event.created_by,
            updated_at=event.updated_at,
            updated_by=event.updated_by,
        )
        return dto

    @staticmethod
    def payload_key_map() -> Dict[str, str]:
        return {
            "title": "title",
            "date": "date",
            "startTime": "start_time",
            "start_time": "start_time",
            "endTime": "end_time",
            "end_time": "end_time",
            "location": "location",
            "locationHint": "location_hint",
            "location_hint": "location_hint",
            "price": "price",
            "fee": "fee",
            "maxParticipants": "max_participants",
            "max_participants": "max_participants",
            "status": "status",
            "image": "image",
            "lineup": "lineup",
            "note": "note",
            "photoPath": "photo_path",
            "photo_path": "photo_path",
            "allowDuplicates": "allow_duplicates",
            "allow_duplicates": "allow_duplicates",
            "over21Only": "over21_only",
            "over21_only": "over21_only",
            "onlyFemales": "only_females",
            "only_females": "only_females",
            "externalLink": "external_link",
            "external_link": "external_link",
            "purchaseMode": "purchase_mode",
            "purchase_mode": "purchase_mode",
            "type": "purchase_mode",
        }

    def resolve_fields_to_apply(self, fields_present: Optional[Set[str]], is_update: bool) -> Set[str]:
        effective_fields = fields_present or self.fields_present
        if not effective_fields:
            return {
                "title",
                "date",
                "start_time",
                "end_time",
                "location",
                "location_hint",
                "price",
                "fee",
                "max_participants",
                "status",
                "image",
                "lineup",
                "note",
                "photo_path",
                "allow_duplicates",
                "over21_only",
                "only_females",
                "external_link",
                "purchase_mode",
            }

        mapping = self.payload_key_map()
        attrs: Set[str] = set()
        for key in effective_fields:
            attr = mapping.get(key)
            if not attr:
                continue
            value = getattr(self, attr, None)
            if is_update and isinstance(value, str) and value.strip() == "":
                continue
            attrs.add(attr)
        return attrs

    def public_payload(self, view: Optional[str] = None) -> Dict[str, Any]:
        if view == "card":
            return {
                "id": self.id,
                "slug": self.slug,
                "title": self.title,
                "date": self.date,
                "startTime": self.start_time,
                "endTime": self.end_time,
                "locationHint": self.location_hint,
                "image": self.image,
                "photoPath": self.photo_path,
                "status": self.status,
            }
        if view == "gallery":
            return {
                "id": self.id,
                "slug": self.slug,
                "title": self.title,
                "date": self.date,
                "photoPath": self.photo_path,
                "image": self.image,
                "status": self.status,
            }
        if view == "ids":
            return {"id": self.id, "slug": self.slug}
        return self.to_payload()

    def membership_event_payload(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "image": self.image,
        }

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "date": self.date,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "locationHint": self.location_hint,
            "location": self.location,
            "price": self.price,
            "fee": self.fee,
            "maxParticipants": self.max_participants,
            "status": self.status,
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
            "createdAt": self.created_at,
            "createdBy": self.created_by,
            "updatedAt": self.updated_at,
            "updatedBy": self.updated_by,
        }
        if self.purchase_mode is not None:
            payload["type"] = self.purchase_mode
        return {k: v for k, v in payload.items() if v is not None}

    def validate(
        self,
        fields_to_apply: Set[str],
        *,
        is_update: bool,
        normalize_date: Optional[Callable[[str], str]] = None,
    ) -> Optional[str]:
        if not is_update:
            required = {"title", "date", "start_time", "location", "location_hint"}
            missing = [field for field in required if not getattr(self, field, None)]
            if missing:
                return f"Missing required fields: {', '.join(missing)}"

        if "date" in fields_to_apply and getattr(self, "date", None):
            if normalize_date:
                normalize_date(self.date)

        if "price" in fields_to_apply and self.price is not None:
            try:
                float(self.price)
            except (ValueError, TypeError):
                return "Invalid price format"

        if "fee" in fields_to_apply and self.fee is not None:
            try:
                float(self.fee)
            except (ValueError, TypeError):
                return "Invalid fee format"

        if "max_participants" in fields_to_apply and self.max_participants is not None:
            try:
                int(self.max_participants)
            except (ValueError, TypeError):
                return "Invalid maxParticipants format"

        return None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "EventDTO":
        dto = cls(
            id=payload.get("id"),
            title=payload.get("title", ""),
            slug=payload.get("slug"),
            date=payload.get("date", ""),
            start_time=payload.get("startTime") or payload.get("start_time"),
            end_time=payload.get("endTime") or payload.get("end_time"),
            location_hint=payload.get("locationHint") or payload.get("location_hint"),
            location=payload.get("location"),
            price=payload.get("price"),
            fee=payload.get("fee"),
            max_participants=payload.get("maxParticipants") or payload.get("max_participants"),
            status=payload.get("status", "active"),
            image=payload.get("image"),
            lineup=payload.get("lineup") if "lineup" in payload else None,
            note=payload.get("note", ""),
            photo_path=payload.get("photoPath") or payload.get("photo_path"),
            purchase_mode=payload.get("purchaseMode")
            or payload.get("purchase_mode")
            or payload.get("type"),
            allow_duplicates=payload.get("allowDuplicates") if "allowDuplicates" in payload else payload.get("allow_duplicates", False),
            over21_only=payload.get("over21Only") if "over21Only" in payload else payload.get("over21_only", False),
            only_females=payload.get("onlyFemales") if "onlyFemales" in payload else payload.get("only_females", False),
            participants_count=payload.get("participantsCount") or payload.get("participants_count", 0),
            external_link=payload.get("externalLink") or payload.get("external_link"),
            created_at=payload.get("createdAt") or payload.get("created_at"),
            created_by=payload.get("createdBy") or payload.get("created_by"),
            updated_at=payload.get("updatedAt") or payload.get("updated_at"),
            updated_by=payload.get("updatedBy") or payload.get("updated_by"),
        )
        dto.fields_present = set(payload.keys())
        return dto
