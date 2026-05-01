from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator


def _blank_to_none(value: Any):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class MessageApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ContactFormRequestDTO(MessageApiBaseDTO):
    name: str = Field(min_length=1)
    email: EmailStr
    message: str = Field(min_length=1)
    subject: Optional[str] = None
    send_copy: bool = Field(default=False, validation_alias=AliasChoices("send_copy", "sendCopy"))
    participant_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("participant_id", "participantId"))
    event_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("event_id", "eventId"))
    error_message: Optional[str] = Field(default=None, validation_alias=AliasChoices("error_message", "errorMessage"))

    @field_validator("subject", "participant_id", "event_id", "error_message", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        return _blank_to_none(value)


class ReplyMessageRequestDTO(MessageApiBaseDTO):
    message_id: str = Field(min_length=1, validation_alias=AliasChoices("message_id", "messageId", "id"))
    email: EmailStr
    body: str = Field(min_length=1)
    subject: Optional[str] = "Risposta al tuo messaggio"

    @field_validator("subject", mode="before")
    @classmethod
    def normalize_subject(cls, value):
        return _blank_to_none(value) or "Risposta al tuo messaggio"


class MessageIdRequestDTO(MessageApiBaseDTO):
    message_id: str = Field(min_length=1, validation_alias=AliasChoices("message_id", "messageId", "id"))


class ContactMessageResponseDTO(MessageApiBaseDTO):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    subject: Optional[str] = None
    answered: bool = False
    participant_id: Optional[str] = None
    event_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[Any] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MessageActionResponseDTO(MessageApiBaseDTO):
    message: Optional[str] = None
    success: Optional[bool] = None
    deleted_id: Optional[str] = Field(default=None, alias="deletedId")
    email_sent_to: Optional[str] = Field(default=None, alias="emailSentTo")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
