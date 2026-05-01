from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from models import AdminUser


class AdminBaseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, str_strip_whitespace=True)


class CreateAdminRequestDTO(AdminBaseDTO):
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str = Field(default="", alias="displayName")

    def to_model(self, created_by: str) -> AdminUser:
        return AdminUser(
            email=str(self.email),
            display_name=self.display_name,
            created_by=created_by,
        )


class UpdateAdminRequestDTO(AdminBaseDTO):
    uid: str = Field(min_length=1)
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(default=None, alias="displayName")

    @model_validator(mode="after")
    def validate_update_fields(self) -> "UpdateAdminRequestDTO":
        if self.email is None and self.display_name is None:
            raise ValueError("At least one field must be provided for update")
        return self

    def apply_to_model(self, admin_user: AdminUser) -> AdminUser:
        if self.email is not None:
            admin_user.email = str(self.email)
        if self.display_name is not None:
            admin_user.display_name = self.display_name
        return admin_user


class AdminIdQueryDTO(AdminBaseDTO):
    id: str = Field(min_length=1)


class AdminResponseDTO(AdminBaseDTO):
    uid: str
    email: str
    display_name: str = Field(default="", serialization_alias="displayName")
    created_at: Optional[Any] = Field(default=None, serialization_alias="createdAt")
    created_by: Optional[str] = Field(default=None, serialization_alias="createdBy")

    @classmethod
    def from_model(cls, admin_user: AdminUser) -> "AdminResponseDTO":
        return cls(
            uid=admin_user.id or "",
            email=admin_user.email,
            display_name=admin_user.display_name,
            created_at=admin_user.created_at,
            created_by=admin_user.created_by,
        )


class AdminListResponseDTO(AdminBaseDTO):
    admins: List[AdminResponseDTO]

    @classmethod
    def from_models(cls, admin_users: List[AdminUser]) -> "AdminListResponseDTO":
        return cls(admins=[AdminResponseDTO.from_model(admin_user) for admin_user in admin_users])


class AdminActionResponseDTO(AdminBaseDTO):
    message: str
    uid: Optional[str] = None
