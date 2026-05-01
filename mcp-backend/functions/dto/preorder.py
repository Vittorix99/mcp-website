from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from utils.events_utils import normalize_email, normalize_phone


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class PaymentApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class CheckoutParticipantDTO(PaymentApiBaseDTO):
    name: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(min_length=1)
    birthdate: Optional[str] = None
    newsletter_consent: bool = Field(
        default=False,
        validation_alias=AliasChoices("newsletterConsent", "newsletter_consent"),
        serialization_alias="newsletterConsent",
    )
    gender: Optional[str] = None
    gender_probability: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("gender_probability", "genderProbability"),
        serialization_alias="gender_probability",
    )

    @field_validator("birthdate", "gender", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value):
        return _blank_to_none(value)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email_field(cls, value: EmailStr) -> str:
        return normalize_email(str(value))

    @field_validator("phone", mode="after")
    @classmethod
    def normalize_phone_field(cls, value: str) -> str:
        return normalize_phone(value)

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class PreOrderCartItemDTO(PaymentApiBaseDTO):
    event_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("eventId", "event_id"),
        serialization_alias="eventId",
    )
    participants: List[CheckoutParticipantDTO] = Field(min_length=1)
    event_meta: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("eventMeta", "event_meta"),
        serialization_alias="eventMeta",
    )

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class PreOrderDTO(PaymentApiBaseDTO):
    cart: List[PreOrderCartItemDTO] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_single_cart_item(self) -> "PreOrderDTO":
        if len(self.cart) != 1:
            raise ValueError("Only one cart item is allowed")
        return self

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class OrderCaptureDTO(PaymentApiBaseDTO):
    order_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("order_id", "orderId"),
        serialization_alias="order_id",
    )

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class EventOrderCreateResponseDTO(PaymentApiBaseDTO):
    id: str
    status: str
    links: List[Dict[str, Any]] = Field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class OrderCaptureResponseDTO(PaymentApiBaseDTO):
    message: str
    purchase_id: str = Field(serialization_alias="purchase_id")
    payment_method: Optional[str] = Field(default=None, serialization_alias="payment_method")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
