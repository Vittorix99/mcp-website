from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.event_rules import normalize_event_date_string
from models import EventPurchaseAccessType, EventStatus


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class EventApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class EventViewQueryDTO(EventApiBaseDTO):
    view: Optional[str] = None

    @field_validator("view", mode="before")
    @classmethod
    def normalize_view(cls, value):
        return _blank_to_none(value)


class EventLookupQueryDTO(EventApiBaseDTO):
    id: Optional[str] = None
    slug: Optional[str] = None

    @field_validator("id", "slug", mode="before")
    @classmethod
    def normalize_identifier(cls, value):
        return _blank_to_none(value)

    @model_validator(mode="after")
    def validate_lookup(self) -> "EventLookupQueryDTO":
        if not self.id and not self.slug:
            raise ValueError("Either id or slug must be provided")
        return self


class EventDeleteRequestDTO(EventApiBaseDTO):
    id: str = Field(min_length=1)


class CreateEventRequestDTO(EventApiBaseDTO):
    title: str = Field(min_length=1)
    location: str = Field(min_length=1)
    location_hint: str = Field(min_length=1, alias="locationHint")
    date: str = Field(min_length=1)
    start_time: str = Field(min_length=1, alias="startTime")
    end_time: Optional[str] = Field(default=None, alias="endTime")
    price: Optional[float] = None
    fee: Optional[float] = None
    max_participants: Optional[int] = Field(default=None, alias="maxParticipants")
    status: EventStatus = EventStatus.ACTIVE
    image: Optional[str] = None
    lineup: List[str] = Field(default_factory=list)
    note: str = ""
    photo_path: Optional[str] = Field(default=None, alias="photoPath")
    purchase_mode: EventPurchaseAccessType = Field(
        default=EventPurchaseAccessType.PUBLIC,
        validation_alias=AliasChoices("purchaseMode", "purchase_mode", "type"),
        serialization_alias="purchaseMode",
    )
    allow_duplicates: bool = Field(default=False, alias="allowDuplicates")
    over21_only: bool = Field(default=False, alias="over21Only")
    only_females: bool = Field(default=False, alias="onlyFemales")
    external_link: Optional[str] = Field(default=None, alias="externalLink")

    @field_validator("date")
    @classmethod
    def normalize_date(cls, value: str) -> str:
        return normalize_event_date_string(value)

    @field_validator(
        "end_time",
        "image",
        "photo_path",
        "external_link",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value):
        return _blank_to_none(value)


class UpdateEventRequestDTO(EventApiBaseDTO):
    id: str = Field(min_length=1)
    title: Optional[str] = None
    location: Optional[str] = None
    location_hint: Optional[str] = Field(default=None, alias="locationHint")
    date: Optional[str] = None
    start_time: Optional[str] = Field(default=None, alias="startTime")
    end_time: Optional[str] = Field(default=None, alias="endTime")
    price: Optional[float] = None
    fee: Optional[float] = None
    max_participants: Optional[int] = Field(default=None, alias="maxParticipants")
    status: Optional[EventStatus] = None
    image: Optional[str] = None
    lineup: Optional[List[str]] = None
    note: Optional[str] = None
    photo_path: Optional[str] = Field(default=None, alias="photoPath")
    purchase_mode: Optional[EventPurchaseAccessType] = Field(
        default=None,
        validation_alias=AliasChoices("purchaseMode", "purchase_mode", "type"),
        serialization_alias="purchaseMode",
    )
    allow_duplicates: Optional[bool] = Field(default=None, alias="allowDuplicates")
    over21_only: Optional[bool] = Field(default=None, alias="over21Only")
    only_females: Optional[bool] = Field(default=None, alias="onlyFemales")
    external_link: Optional[str] = Field(default=None, alias="externalLink")

    @field_validator(
        "title",
        "location",
        "location_hint",
        "date",
        "start_time",
        "end_time",
        "image",
        "note",
        "photo_path",
        "external_link",
        mode="before",
    )
    @classmethod
    def normalize_optional_fields(cls, value):
        return _blank_to_none(value)

    @field_validator("date")
    @classmethod
    def normalize_optional_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_event_date_string(value)

    @model_validator(mode="after")
    def validate_update_fields(self) -> "UpdateEventRequestDTO":
        if not self.changes():
            raise ValueError("At least one field must be provided for update")
        return self

    def changes(self) -> Dict[str, Any]:
        allowed_fields: Set[str] = set(self.model_fields_set) - {"id"}
        return {
            field_name: getattr(self, field_name)
            for field_name in allowed_fields
        }


class EventActionResponseDTO(EventApiBaseDTO):
    message: str
    event_id: str = Field(serialization_alias="eventId")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class AdminEventResponseDTO(EventApiBaseDTO):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
    )

    id: Optional[str] = None
    title: str
    slug: Optional[str] = None
    date: str
    start_time: Optional[str] = Field(default=None, serialization_alias="startTime")
    end_time: Optional[str] = Field(default=None, serialization_alias="endTime")
    location_hint: Optional[str] = Field(default=None, serialization_alias="locationHint")
    location: Optional[str] = None
    price: Optional[float] = None
    fee: Optional[float] = None
    max_participants: Optional[int] = Field(default=None, serialization_alias="maxParticipants")
    status: EventStatus = EventStatus.ACTIVE
    image: Optional[str] = None
    lineup: List[str] = Field(default_factory=list)
    note: str = ""
    photo_path: Optional[str] = Field(default=None, serialization_alias="photoPath")
    purchase_mode: EventPurchaseAccessType = Field(
        default=EventPurchaseAccessType.PUBLIC,
        serialization_alias="purchaseMode",
    )
    allow_duplicates: bool = Field(default=False, serialization_alias="allowDuplicates")
    over21_only: bool = Field(default=False, serialization_alias="over21Only")
    only_females: bool = Field(default=False, serialization_alias="onlyFemales")
    participants_count: int = Field(default=0, serialization_alias="participantsCount")
    external_link: Optional[str] = Field(default=None, serialization_alias="externalLink")
    created_at: Optional[Any] = Field(default=None, serialization_alias="createdAt")
    created_by: Optional[str] = Field(default=None, serialization_alias="createdBy")
    updated_at: Optional[Any] = Field(default=None, serialization_alias="updatedAt")
    updated_by: Optional[str] = Field(default=None, serialization_alias="updatedBy")

    def to_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(by_alias=True, exclude_none=True)
        payload["type"] = payload.get("purchaseMode")
        return payload


class AdminEventEnvelopeResponseDTO(EventApiBaseDTO):
    event: AdminEventResponseDTO

    def to_payload(self) -> Dict[str, Any]:
        return {"event": self.event.to_payload()}


class PublicEventResponseDTO(EventApiBaseDTO):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
    )

    id: Optional[str] = None
    slug: Optional[str] = None
    title: str
    date: str
    start_time: Optional[str] = Field(default=None, serialization_alias="startTime")
    end_time: Optional[str] = Field(default=None, serialization_alias="endTime")
    location_hint: Optional[str] = Field(default=None, serialization_alias="locationHint")
    price: Optional[float] = None
    fee: Optional[float] = None
    status: EventStatus = EventStatus.ACTIVE
    image: Optional[str] = None
    lineup: List[str] = Field(default_factory=list)
    note: str = ""
    photo_path: Optional[str] = Field(default=None, serialization_alias="photoPath")
    purchase_mode: EventPurchaseAccessType = Field(
        default=EventPurchaseAccessType.PUBLIC,
        serialization_alias="purchaseMode",
    )
    allow_duplicates: bool = Field(default=False, serialization_alias="allowDuplicates")
    over21_only: bool = Field(default=False, serialization_alias="over21Only")
    only_females: bool = Field(default=False, serialization_alias="onlyFemales")
    external_link: Optional[str] = Field(default=None, serialization_alias="externalLink")
    created_at: Optional[Any] = Field(default=None, serialization_alias="createdAt")
    updated_at: Optional[Any] = Field(default=None, serialization_alias="updatedAt")

    def to_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(by_alias=True, exclude_none=True)
        payload["type"] = payload.get("purchaseMode") # This is needed for backward compatibility with the old "type" field used in the frontend for purchase mode
        return payload

    def to_view_payload(self, view: Optional[str] = None) -> Dict[str, Any]:
        payload = self.to_payload()
        if view == "card":
            keys = {"id", "slug", "title", "date", "startTime", "endTime", "locationHint", "image", "photoPath", "status"}
            return {key: payload[key] for key in keys if key in payload}
        if view == "gallery":
            keys = {"id", "slug", "title", "date", "photoPath", "image", "status"}
            return {key: payload[key] for key in keys if key in payload}
        if view == "ids":
            keys = {"id", "slug"}
            return {key: payload[key] for key in keys if key in payload}
        return payload
