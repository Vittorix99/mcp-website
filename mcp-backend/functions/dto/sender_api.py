from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class SenderApiBaseDTO(BaseModel):
    """Base for mutation endpoints (POST/PUT/DELETE) — strict validation."""
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class SenderQueryBaseDTO(BaseModel):
    """Base for GET endpoints that proxy to Sender.net — unknown query params are ignored."""
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── Subscriber DTOs ───────────────────────────────────────────────────────────

class SubscriberQueryDTO(SenderQueryBaseDTO):
    email: Optional[EmailStr] = None


class UpsertSubscriberRequestDTO(SenderApiBaseDTO):
    email: EmailStr
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    groups: Optional[List[str]] = None
    fields: Optional[Dict[str, Any]] = None


class UpdateSubscriberRequestDTO(SenderApiBaseDTO):
    email: EmailStr
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None

    def changes(self) -> Dict[str, Any]:
        allowed = set(self.model_fields_set) - {"email"}
        return {k: getattr(self, k) for k in allowed}


class DeleteSubscriberRequestDTO(SenderApiBaseDTO):
    email: EmailStr


class SubscriberGroupRequestDTO(SenderApiBaseDTO):
    email: EmailStr
    group_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("group_id", "groupId"),
        serialization_alias="groupId",
    )


class SubscriberEventQueryDTO(SenderQueryBaseDTO):
    email: Optional[EmailStr] = None
    id: Optional[str] = None
    actions: Optional[str] = None

    @model_validator(mode="after")
    def validate_identifier(self) -> "SubscriberEventQueryDTO":
        if not self.email and not self.id:
            raise ValueError("Either email or id must be provided")
        return self


# ── Group DTOs ────────────────────────────────────────────────────────────────

class CreateGroupRequestDTO(SenderApiBaseDTO):
    title: str = Field(min_length=1, validation_alias=AliasChoices("title", "name"))


class UpdateGroupRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "group_id", "groupId"))
    title: str = Field(min_length=1, validation_alias=AliasChoices("title", "name"))


class GroupDeleteRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "group_id", "groupId"))


class GroupSubscribersQueryDTO(SenderQueryBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "group_id", "groupId"))


# ── Campaign DTOs ─────────────────────────────────────────────────────────────

class CampaignQueryDTO(SenderQueryBaseDTO):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("id", "campaign_id", "campaignId"),
    )


class CreateCampaignRequestDTO(SenderApiBaseDTO):
    title: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    from_name: str = Field(min_length=1, validation_alias=AliasChoices("from_name", "fromName"))
    from_email: EmailStr = Field(validation_alias=AliasChoices("from_email", "fromEmail"))
    content_html: str = Field(min_length=1, validation_alias=AliasChoices("content_html", "html"))
    reply_to: Optional[EmailStr] = Field(default=None, validation_alias=AliasChoices("reply_to", "replyTo"))
    groups: Optional[List[str]] = None


class UpdateCampaignRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "campaign_id", "campaignId"))
    title: Optional[str] = None
    subject: Optional[str] = None
    from_name: Optional[str] = Field(default=None, validation_alias=AliasChoices("from_name", "fromName"))
    from_email: Optional[EmailStr] = Field(default=None, validation_alias=AliasChoices("from_email", "fromEmail"))
    content_html: Optional[str] = Field(default=None, validation_alias=AliasChoices("content_html", "html"))
    groups: Optional[List[str]] = None


class CampaignIdRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "campaign_id", "campaignId"))


class ScheduleCampaignRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "campaign_id", "campaignId"))
    scheduled_at: str = Field(min_length=1, validation_alias=AliasChoices("scheduled_at", "scheduledAt"))


class CampaignStatsQueryDTO(SenderQueryBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "campaign_id", "campaignId"))
    type: str = "opens"

    @field_validator("type")
    @classmethod
    def validate_stat_type(cls, v: str) -> str:
        allowed = {"opens", "clicks", "unsubscribes", "bounces_hard", "bounces_soft"}
        if v not in allowed:
            raise ValueError(f"Unknown stat type '{v}'. Allowed: {sorted(allowed)}")
        return v


# ── Field DTOs ────────────────────────────────────────────────────────────────

class CreateFieldRequestDTO(SenderApiBaseDTO):
    title: str = Field(min_length=1)
    type: str = Field(default="string", validation_alias=AliasChoices("type", "field_type"))


class FieldDeleteRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "field_id"))


# ── Segment DTOs ──────────────────────────────────────────────────────────────

class SegmentQueryDTO(SenderQueryBaseDTO):
    id: Optional[str] = Field(default=None, validation_alias=AliasChoices("id", "segment_id"))


class SegmentDeleteRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "segment_id"))


class SegmentSubscribersQueryDTO(SenderQueryBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "segment_id"))


# ── Transactional DTOs ────────────────────────────────────────────────────────

class CreateTransactionalCampaignRequestDTO(SenderApiBaseDTO):
    title: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    from_name: str = Field(min_length=1, validation_alias=AliasChoices("from_name", "fromName"))
    from_email: EmailStr = Field(validation_alias=AliasChoices("from_email", "fromEmail"))
    content_html: str = Field(min_length=1, validation_alias=AliasChoices("content_html", "html"))


class SendTransactionalCampaignRequestDTO(SenderApiBaseDTO):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "campaign_id", "campaignId"))
    to_email: EmailStr = Field(validation_alias=AliasChoices("to_email", "toEmail"))
    to_name: str = Field(default="", validation_alias=AliasChoices("to_name", "toName"))
    variables: Optional[Dict[str, Any]] = None
