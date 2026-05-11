from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class DiscountCodeApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class DiscountCodeEventRequestDTO(DiscountCodeApiBaseDTO):
    event_id: str = Field(min_length=1, validation_alias=AliasChoices("event_id", "eventId"))


class DiscountCodeIdRequestDTO(DiscountCodeApiBaseDTO):
    discount_code_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("discount_code_id", "discountCodeId", "id"),
    )


class CreateDiscountCodeRequestDTO(DiscountCodeApiBaseDTO):
    code: str = Field(min_length=1)
    discount_type: str = Field(validation_alias=AliasChoices("discount_type", "discountType"))
    discount_value: float = Field(gt=0, validation_alias=AliasChoices("discount_value", "discountValue"))
    max_uses: int = Field(ge=1, validation_alias=AliasChoices("max_uses", "maxUses"))
    restricted_membership_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("restricted_membership_id", "restrictedMembershipId"),
    )
    restricted_email: Optional[EmailStr] = Field(
        default=None,
        validation_alias=AliasChoices("restricted_email", "restrictedEmail"),
    )

    @field_validator("code", "discount_type", "restricted_membership_id", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        return _blank_to_none(value)

    @field_validator("restricted_email", mode="after")
    @classmethod
    def normalize_restricted_email(cls, value: Optional[EmailStr]) -> Optional[str]:
        return str(value).lower() if value is not None else None

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, value: str) -> str:
        allowed = {"PERCENTAGE", "FIXED", "FIXED_PRICE"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError("Invalid discount_type")
        return normalized

    @model_validator(mode="after")
    def check_mutual_exclusivity(self) -> "CreateDiscountCodeRequestDTO":
        if self.restricted_membership_id and self.restricted_email:
            raise ValueError("restricted_membership_id e restricted_email sono mutualmente esclusivi")
        return self

    def to_repository_data(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class AdminCreateDiscountCodeRequestDTO(CreateDiscountCodeRequestDTO):
    event_id: str = Field(min_length=1, validation_alias=AliasChoices("event_id", "eventId"))


class UpdateDiscountCodeRequestDTO(DiscountCodeApiBaseDTO):
    is_active: Optional[bool] = Field(default=None, validation_alias=AliasChoices("is_active", "isActive"))
    max_uses: Optional[int] = Field(default=None, ge=1, validation_alias=AliasChoices("max_uses", "maxUses"))
    discount_value: Optional[float] = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("discount_value", "discountValue"),
    )
    discount_type: Optional[str] = Field(default=None, validation_alias=AliasChoices("discount_type", "discountType"))
    restricted_membership_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("restricted_membership_id", "restrictedMembershipId"),
    )
    restricted_email: Optional[EmailStr] = Field(
        default=None,
        validation_alias=AliasChoices("restricted_email", "restrictedEmail"),
    )

    @field_validator("discount_type", "restricted_membership_id", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        return _blank_to_none(value)

    @field_validator("restricted_email", mode="after")
    @classmethod
    def normalize_restricted_email(cls, value: Optional[EmailStr]) -> Optional[str]:
        return str(value).lower() if value is not None else None

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        allowed = {"PERCENTAGE", "FIXED", "FIXED_PRICE"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError("Invalid discount_type")
        return normalized

    @model_validator(mode="after")
    def check_update_fields(self) -> "UpdateDiscountCodeRequestDTO":
        if self.restricted_membership_id and self.restricted_email:
            raise ValueError("restricted_membership_id e restricted_email sono mutualmente esclusivi")
        if not self.changes():
            raise ValueError("At least one field must be provided for update")
        return self

    def changes(self) -> Dict[str, Any]:
        return {field: getattr(self, field) for field in self.model_fields_set}


class AdminUpdateDiscountCodeRequestDTO(UpdateDiscountCodeRequestDTO):
    discount_code_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("discount_code_id", "discountCodeId", "id"),
    )

    def changes(self) -> Dict[str, Any]:
        return {field: getattr(self, field) for field in self.model_fields_set if field != "discount_code_id"}


class ValidateDiscountCodeRequestDTO(DiscountCodeEventRequestDTO):
    code: str = Field(min_length=1)
    participants_count: int = Field(ge=1, validation_alias=AliasChoices("participants_count", "participantsCount"))
    payer_email: EmailStr = Field(validation_alias=AliasChoices("payer_email", "payerEmail"))
    payer_membership_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("payer_membership_id", "payerMembershipId"),
    )

    @field_validator("code", "payer_membership_id", mode="before")
    @classmethod
    def normalize_strings(cls, value):
        return _blank_to_none(value)

    @field_validator("payer_email", mode="after")
    @classmethod
    def normalize_payer_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class DiscountCodeResponseDTO(DiscountCodeApiBaseDTO):
    id: str
    event_id: str = Field(serialization_alias="event_id")
    code: str
    discount_type: str = Field(serialization_alias="discount_type")
    discount_value: float = Field(serialization_alias="discount_value")
    max_uses: int = Field(serialization_alias="max_uses")
    used_count: int = Field(serialization_alias="used_count")
    is_active: bool = Field(serialization_alias="is_active")
    restricted_membership_id: Optional[str] = Field(default=None, serialization_alias="restricted_membership_id")
    restricted_email: Optional[str] = Field(default=None, serialization_alias="restricted_email")
    created_at: Optional[Any] = Field(default=None, serialization_alias="created_at")
    updated_at: Optional[Any] = Field(default=None, serialization_alias="updated_at")

    def to_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(by_alias=True, exclude_none=True)
        payload.update(
            {
                "eventId": payload.get("event_id"),
                "discountType": payload.get("discount_type"),
                "discountValue": payload.get("discount_value"),
                "maxUses": payload.get("max_uses"),
                "usedCount": payload.get("used_count"),
                "isActive": payload.get("is_active"),
                "restrictedMembershipId": payload.get("restricted_membership_id"),
                "restrictedEmail": payload.get("restricted_email"),
                "createdAt": payload.get("created_at"),
                "updatedAt": payload.get("updated_at"),
            }
        )
        return {key: value for key, value in payload.items() if value is not None}


class ValidateDiscountCodeResponseDTO(DiscountCodeApiBaseDTO):
    valid: bool
    discount_code_id: Optional[str] = Field(default=None, serialization_alias="discount_code_id")
    code: Optional[str] = None
    discount_type: Optional[str] = Field(default=None, serialization_alias="discount_type")
    discount_value: Optional[float] = Field(default=None, serialization_alias="discount_value")
    discount_amount: Optional[float] = Field(default=None, serialization_alias="discount_amount")
    final_price: Optional[float] = Field(default=None, serialization_alias="final_price")
    error_message: Optional[str] = Field(default=None, serialization_alias="error_message")

    def to_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(by_alias=True, exclude_none=True)
        payload.update(
            {
                "discountCodeId": payload.get("discount_code_id"),
                "discountType": payload.get("discount_type"),
                "discountValue": payload.get("discount_value"),
                "discountAmount": payload.get("discount_amount"),
                "finalPrice": payload.get("final_price"),
                "errorMessage": payload.get("error_message"),
            }
        )
        return {key: value for key, value in payload.items() if value is not None}
