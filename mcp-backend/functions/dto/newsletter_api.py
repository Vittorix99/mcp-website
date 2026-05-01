from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class NewsletterApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── Request DTOs ──────────────────────────────────────────────────────────────

class NewsletterSignupRequestDTO(NewsletterApiBaseDTO):
    email: EmailStr
    name: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Any) -> Any:
        return _blank_to_none(value)


class NewsletterUpdateRequestDTO(NewsletterApiBaseDTO):
    id: str = Field(min_length=1)
    active: bool


class NewsletterDeleteQueryDTO(NewsletterApiBaseDTO):
    id: str = Field(min_length=1)


class NewsletterLookupQueryDTO(NewsletterApiBaseDTO):
    id: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> Any:
        return _blank_to_none(value)


class NewsletterParticipantItemDTO(BaseModel):
    """Single participant entry in a bulk-add request. Extra fields are preserved."""
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )
    email: EmailStr

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class NewsletterParticipantsRequestDTO(NewsletterApiBaseDTO):
    participants: List[NewsletterParticipantItemDTO] = Field(min_length=1)


# ── Response DTOs ─────────────────────────────────────────────────────────────

class NewsletterActionResponseDTO(NewsletterApiBaseDTO):
    message: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class NewsletterSignupResponseDTO(NewsletterApiBaseDTO):
    id: Optional[str] = None
    email: str
    timestamp: Optional[Any] = None
    active: bool = True
    source: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class NewsletterSignupEnvelopeResponseDTO(NewsletterApiBaseDTO):
    signup: NewsletterSignupResponseDTO

    def to_payload(self) -> Dict[str, Any]:
        return {"signup": self.signup.to_payload()}


class NewsletterSignupsListResponseDTO(NewsletterApiBaseDTO):
    signups: List[NewsletterSignupResponseDTO]

    def to_payload(self) -> Dict[str, Any]:
        return {"signups": [s.to_payload() for s in self.signups]}


class NewsletterConsentResponseDTO(NewsletterApiBaseDTO):
    id: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = Field(default=None, serialization_alias="genderProbability")
    event_id: Optional[str] = Field(default=None, serialization_alias="eventId")
    participant_id: Optional[str] = Field(default=None, serialization_alias="participantId")
    timestamp: Optional[Any] = None
    source: str = "participant_event"
    active: bool = True

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class NewsletterConsentsListResponseDTO(NewsletterApiBaseDTO):
    consents: List[NewsletterConsentResponseDTO]

    def to_payload(self) -> Dict[str, Any]:
        return {"consents": [c.to_payload() for c in self.consents]}
