from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from utils.events_utils import normalize_email, normalize_phone


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class MembershipApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class MembershipListQueryDTO(MembershipApiBaseDTO):
    year: Optional[int] = None

    @field_validator("year", mode="before")
    @classmethod
    def normalize_year(cls, value):
        return _blank_to_none(value)


class MembershipLookupQueryDTO(MembershipApiBaseDTO):
    id: Optional[str] = None
    slug: Optional[str] = None

    @field_validator("id", "slug", mode="before")
    @classmethod
    def normalize_lookup_fields(cls, value):
        return _blank_to_none(value)

    @model_validator(mode="after")
    def validate_lookup(self) -> "MembershipLookupQueryDTO":
        if not self.id and not self.slug:
            raise ValueError("Either id or slug must be provided")
        return self


class MembershipIdRequestDTO(MembershipApiBaseDTO):
    membership_id: str = Field(min_length=1, validation_alias=AliasChoices("membership_id", "membershipId", "id"))


class CreateMembershipRequestDTO(MembershipApiBaseDTO):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    membership_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("membership_type", "membershipType"),
        serialization_alias="membership_type",
    )
    purchase_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("purchase_id", "purchaseId"),
        serialization_alias="purchase_id",
    )
    send_card_on_create: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("send_card_on_create", "sendCardOnCreate"),
        serialization_alias="send_card_on_create",
    )
    membership_fee: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("membership_fee", "membershipFee"),
        serialization_alias="membership_fee",
    )

    @field_validator("name", "surname", "phone", "birthdate", "membership_type", "purchase_id", mode="before")
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


class UpdateMembershipRequestDTO(CreateMembershipRequestDTO):
    membership_id: str = Field(min_length=1, validation_alias=AliasChoices("membership_id", "membershipId", "id"))

    @model_validator(mode="after")
    def validate_update_fields(self) -> "UpdateMembershipRequestDTO":
        if not self.changes():
            raise ValueError("At least one field must be provided for update")
        return self

    def changes(self) -> Dict[str, Any]:
        allowed_fields: Set[str] = set(self.model_fields_set) - {"membership_id"}
        return {field_name: getattr(self, field_name) for field_name in allowed_fields}


class RenewMembershipRequestDTO(MembershipApiBaseDTO):
    membership_id: str = Field(min_length=1, validation_alias=AliasChoices("membership_id", "membershipId", "id"))
    purchase_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("purchase_id", "purchaseId"),
        serialization_alias="purchase_id",
    )
    membership_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("membership_type", "membershipType"),
        serialization_alias="membership_type",
    )
    send_card_on_create: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("send_card_on_create", "sendCardOnCreate"),
        serialization_alias="send_card_on_create",
    )
    membership_fee: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("membership_fee", "membershipFee"),
        serialization_alias="membership_fee",
    )

    @field_validator("purchase_id", "membership_type", mode="before")
    @classmethod
    def normalize_renew_optional_strings(cls, value):
        return _blank_to_none(value)


class MergeMembershipsRequestDTO(MembershipApiBaseDTO):
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)


class MembershipPriceSetRequestDTO(MembershipApiBaseDTO):
    membership_fee: float = Field(validation_alias=AliasChoices("membership_fee", "membershipFee"))
    year: Optional[int] = None

    @field_validator("year", mode="before")
    @classmethod
    def normalize_price_year(cls, value):
        return _blank_to_none(value)


class MembershipPriceQueryDTO(MembershipApiBaseDTO):
    year: Optional[int] = None

    @field_validator("year", mode="before")
    @classmethod
    def normalize_query_year(cls, value):
        return _blank_to_none(value)


class WalletModelSetRequestDTO(MembershipApiBaseDTO):
    model_id: str = Field(min_length=1, validation_alias=AliasChoices("model_id", "modelId"))


class MembershipReportQueryDTO(MembershipApiBaseDTO):
    event_id: str = Field(min_length=1, validation_alias=AliasChoices("event_id", "eventId"))


class MembershipResponseDTO(MembershipApiBaseDTO):
    id: Optional[str] = None
    name: str = ""
    surname: str = ""
    slug: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    subscription_valid: bool = True
    membership_sent: bool = False
    membership_type: str = "manual"
    purchase_id: Optional[str] = None
    purchases: List[str] = Field(default_factory=list)
    attended_events: List[str] = Field(default_factory=list)
    renewals: List[Dict[str, Any]] = Field(default_factory=list)
    membership_years: List[int] = Field(default_factory=list)
    card_url: Optional[str] = None
    card_storage_path: Optional[str] = None
    send_card_on_create: bool = False
    membership_fee: Optional[float] = None
    wallet_pass_id: Optional[str] = None
    wallet_url: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MembershipActionResponseDTO(MembershipApiBaseDTO):
    message: str
    id: Optional[str] = None
    renewed: Optional[bool] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MembershipPriceResponseDTO(MembershipApiBaseDTO):
    year: str
    price: float
    message: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MembershipWalletPassResponseDTO(MembershipApiBaseDTO):
    wallet_pass_id: str
    wallet_url: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class WalletModelResponseDTO(MembershipApiBaseDTO):
    model_id: str
    message: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
