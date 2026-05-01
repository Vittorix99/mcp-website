from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from models import PaymentMethod
from utils.events_utils import normalize_email, normalize_phone


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ParticipantApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ParticipantEventRequestDTO(ParticipantApiBaseDTO):
    event_id: str = Field(min_length=1, validation_alias=AliasChoices("event_id", "eventId"))


class ParticipantLookupRequestDTO(ParticipantEventRequestDTO):
    participant_id: str = Field(min_length=1, validation_alias=AliasChoices("participant_id", "participantId", "id"))


class ParticipantCreateRequestDTO(ParticipantEventRequestDTO):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    membership_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("membership_id", "membershipId"))
    membership_included: Optional[bool] = Field(default=None, validation_alias=AliasChoices("membership_included", "membershipIncluded"))
    ticket_sent: Optional[bool] = Field(default=None, validation_alias=AliasChoices("ticket_sent", "ticketSent"))
    send_ticket_on_create: Optional[bool] = Field(default=None, validation_alias=AliasChoices("send_ticket_on_create", "sendTicketOnCreate"))
    location_sent: Optional[bool] = Field(default=None, validation_alias=AliasChoices("location_sent", "locationSent"))
    newsletter_consent: Optional[bool] = Field(default=None, validation_alias=AliasChoices("newsletter_consent", "newsletterConsent"))
    price: Optional[float] = None
    payment_method: Optional[str] = Field(default=None, validation_alias=AliasChoices("payment_method", "paymentMethod"))
    purchase_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("purchase_id", "purchaseId"))
    riduzione: Optional[bool] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = Field(default=None, validation_alias=AliasChoices("gender_probability", "genderProbability"))

    @field_validator(
        "name",
        "surname",
        "phone",
        "birthdate",
        "membership_id",
        "payment_method",
        "purchase_id",
        "gender",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value):
        return _blank_to_none(value)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email_field(cls, value: Optional[EmailStr]) -> Optional[str]:
        if value is None:
            return None
        return normalize_email(str(value)) or None

    @field_validator("phone", mode="after")
    @classmethod
    def normalize_phone_field(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_phone(value) or None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        allowed = {method.value for method in PaymentMethod}
        if value not in allowed:
            raise ValueError("Invalid payment_method")
        return value


class ParticipantUpdateRequestDTO(ParticipantCreateRequestDTO):
    participant_id: str = Field(min_length=1, validation_alias=AliasChoices("participant_id", "participantId", "id"))

    @model_validator(mode="after")
    def validate_update_fields(self) -> "ParticipantUpdateRequestDTO":
        if not self.changes():
            raise ValueError("At least one field must be provided for update")
        return self

    def changes(self) -> Dict[str, Any]:
        allowed_fields: Set[str] = set(self.model_fields_set) - {"event_id", "participant_id"}
        return {field_name: getattr(self, field_name) for field_name in allowed_fields}


class SendTicketRequestDTO(ParticipantLookupRequestDTO):
    pass


class SendLocationRequestDTO(ParticipantLookupRequestDTO):
    address: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None

    @field_validator("address", "link", "message", mode="before")
    @classmethod
    def normalize_send_location_fields(cls, value):
        return _blank_to_none(value)


class SendLocationToAllRequestDTO(ParticipantEventRequestDTO):
    address: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None

    @field_validator("address", "link", "message", mode="before")
    @classmethod
    def normalize_send_location_to_all_fields(cls, value):
        return _blank_to_none(value)


class SendOmaggioEmailsRequestDTO(ParticipantEventRequestDTO):
    entry_time: Optional[str] = Field(default=None, validation_alias=AliasChoices("entry_time", "entryTime"))
    participant_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("participant_id", "participantId"))
    skip_already_sent: bool = Field(default=True, validation_alias=AliasChoices("skip_already_sent", "skipAlreadySent"))

    @field_validator("entry_time", "participant_id", mode="before")
    @classmethod
    def normalize_omaggio_fields(cls, value):
        return _blank_to_none(value)


class CheckoutParticipantRequestDTO(ParticipantApiBaseDTO):
    name: str = ""
    surname: str = ""
    email: str = ""
    phone: str = ""
    birthdate: Optional[str] = None
    newsletter_consent: bool = Field(default=False, validation_alias=AliasChoices("newsletter_consent", "newsletterConsent"))
    gender: Optional[str] = None
    gender_probability: Optional[float] = Field(default=None, validation_alias=AliasChoices("gender_probability", "genderProbability"))


class CheckParticipantsRequestDTO(ParticipantEventRequestDTO):
    participants: List[CheckoutParticipantRequestDTO]


class ParticipantResponseDTO(ParticipantApiBaseDTO):
    id: Optional[str] = None
    event_id: str = ""
    name: str = ""
    surname: str = ""
    email: str = ""
    phone: str = ""
    birthdate: Optional[str] = None
    membership_id: Optional[str] = Field(default=None, serialization_alias="membershipId")
    membership_included: bool = False
    entered: bool = False
    entered_at: Optional[Any] = None
    ticket_pdf_url: Optional[str] = None
    ticket_sent: bool = False
    send_ticket_on_create: bool = False
    location_sent: bool = False
    location_sent_at: Optional[Any] = None
    location_job_id: Optional[str] = None
    omaggio_email_sent: bool = False
    omaggio_email_sent_at: Optional[Any] = None
    gender: Optional[str] = None
    gender_probability: Optional[float] = None
    newsletter_consent: bool = Field(default=False, serialization_alias="newsletterConsent")
    price: Optional[float] = None
    payment_method: Optional[str] = None
    purchase_id: Optional[str] = None
    riduzione: bool = False
    created_at: Optional[Any] = Field(default=None, serialization_alias="createdAt")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class ParticipantActionResponseDTO(ParticipantApiBaseDTO):
    message: str
    id: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class LocationActionResponseDTO(ParticipantApiBaseDTO):
    message: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump()


class LocationBulkActionResponseDTO(ParticipantApiBaseDTO):
    message: str
    success: int
    failures: int

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump()


class LocationJobResponseDTO(ParticipantApiBaseDTO):
    message: str
    job_id: str = Field(serialization_alias="jobId")
    total: int
    status: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class SendOmaggioEmailsResponseDTO(ParticipantApiBaseDTO):
    sent: int
    failed: int
    skipped: int
    total: int
    mode: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump()


class CheckParticipantsResponseDTO(ParticipantApiBaseDTO):
    valid: bool
    members: List[str] = Field(default_factory=list)
    non_members: List[str] = Field(default_factory=list, serialization_alias="nonMembers")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
