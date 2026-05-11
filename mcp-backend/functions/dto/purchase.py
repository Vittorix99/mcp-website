from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from models import EventPurchaseAccessType, PurchaseTypes
from utils.events_utils import normalize_email


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class PurchaseApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class PurchaseLookupQueryDTO(PurchaseApiBaseDTO):
    id: Optional[str] = Field(default=None, validation_alias=AliasChoices("id", "purchase_id"))
    slug: Optional[str] = None

    @field_validator("id", "slug", mode="before")
    @classmethod
    def normalize_lookup_fields(cls, value):
        return _blank_to_none(value)

    @model_validator(mode="after")
    def validate_lookup(self) -> "PurchaseLookupQueryDTO":
        if not self.id and not self.slug:
            raise ValueError("Either id or slug must be provided")
        return self


class PurchaseIdRequestDTO(PurchaseApiBaseDTO):
    purchase_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("purchase_id", "purchaseId", "id"),
        serialization_alias="purchase_id",
    )


class CreatePurchaseRequestDTO(PurchaseApiBaseDTO):
    payer_name: str = Field(min_length=1)
    payer_surname: str = Field(min_length=1)
    payer_email: EmailStr = Field(validation_alias=AliasChoices("payer_email", "payerEmail"))
    amount_total: str = Field(min_length=1, validation_alias=AliasChoices("amount_total", "amountTotal"))
    currency: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1, validation_alias=AliasChoices("transaction_id", "transactionId"))
    order_id: str = Field(min_length=1, validation_alias=AliasChoices("order_id", "orderId"))
    timestamp: Any
    purchase_type: PurchaseTypes = Field(
        default=PurchaseTypes.EVENT,
        validation_alias=AliasChoices("type", "purchase_type", "purchaseType"),
        serialization_alias="type",
    )
    status: str = "COMPLETED"
    slug: Optional[str] = None
    paypal_fee: Optional[str] = Field(default=None, validation_alias=AliasChoices("paypal_fee", "paypalFee"))
    net_amount: Optional[str] = Field(default=None, validation_alias=AliasChoices("net_amount", "netAmount"))
    ref_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("ref_id", "refId"))
    payment_method: Optional[str] = Field(default=None, validation_alias=AliasChoices("payment_method", "paymentMethod"))
    capture_status: Optional[str] = Field(default=None, validation_alias=AliasChoices("capture_status", "captureStatus"))
    event_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("event_id", "eventId"))
    event_purchase_type: Optional[EventPurchaseAccessType] = Field(
        default=None,
        validation_alias=AliasChoices("event_purchase_type", "eventPurchaseType"),
    )
    participants_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("participants_count", "participantsCount"),
    )
    membership_ids: List[str] = Field(default_factory=list)
    discount_code_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("discount_code_id", "discountCodeId"))
    discount_code: Optional[str] = Field(default=None, validation_alias=AliasChoices("discount_code", "discountCode"))
    discount_amount: Optional[float] = Field(default=None, validation_alias=AliasChoices("discount_amount", "discountAmount"))

    @field_validator(
        "slug",
        "paypal_fee",
        "net_amount",
        "ref_id",
        "payment_method",
        "capture_status",
        "event_id",
        "discount_code_id",
        "discount_code",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value):
        return _blank_to_none(value)

    @field_validator("payer_email", mode="after")
    @classmethod
    def normalize_email_field(cls, value: EmailStr) -> str:
        return normalize_email(str(value))


class PurchaseDTO(PurchaseApiBaseDTO):
    id: Optional[str] = None
    payer_name: str
    payer_surname: str
    slug: Optional[str] = None
    payer_email: str
    amount_total: str
    currency: str
    paypal_fee: Optional[str] = None
    net_amount: Optional[str] = None
    transaction_id: str
    order_id: str
    status: str
    timestamp: Optional[Any] = None
    purchase_type: PurchaseTypes = Field(serialization_alias="type")
    ref_id: Optional[str] = None
    payment_method: Optional[str] = None
    capture_status: Optional[str] = None
    event_id: Optional[str] = Field(default=None, serialization_alias="event_id")
    event_purchase_type: Optional[EventPurchaseAccessType] = Field(default=None, serialization_alias="eventPurchaseType")
    participants_count: Optional[int] = Field(default=None, serialization_alias="participants_count")
    membership_ids: List[str] = Field(default_factory=list, serialization_alias="membership_ids")
    discount_code_id: Optional[str] = Field(default=None, serialization_alias="discountCodeId")
    discount_code: Optional[str] = Field(default=None, serialization_alias="discountCode")
    discount_amount: Optional[float] = Field(default=None, serialization_alias="discountAmount")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class PurchaseActionResponseDTO(PurchaseApiBaseDTO):
    message: str
    id: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
