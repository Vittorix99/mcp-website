from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntranceApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── Request DTOs ──────────────────────────────────────────────────────────────

class GenerateScanTokenRequestDTO(EntranceApiBaseDTO):
    event_id: str = Field(min_length=1)


class VerifyScanTokenQueryDTO(EntranceApiBaseDTO):
    token: str = Field(min_length=1)


class DeactivateScanTokenRequestDTO(EntranceApiBaseDTO):
    token: str = Field(min_length=1)


class ManualEntryRequestDTO(EntranceApiBaseDTO):
    event_id: str = Field(min_length=1)
    membership_id: str = Field(min_length=1)
    entered: bool


class ValidateEntryRequestDTO(EntranceApiBaseDTO):
    membership_id: str = Field(min_length=1)
    scan_token: str = Field(min_length=1)


# ── Response DTOs ─────────────────────────────────────────────────────────────

class GenerateScanTokenResponseDTO(EntranceApiBaseDTO):
    token: str
    scan_url: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class VerifyScanTokenResponseDTO(EntranceApiBaseDTO):
    valid: bool
    reason: Optional[str] = None
    event_id: Optional[str] = None
    event_title: Optional[str] = None
    participants_count: Optional[int] = None
    entered_count: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        if not self.valid:
            return {"valid": False, "reason": self.reason}
        return {
            "valid": True,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "participants_count": self.participants_count,
            "entered_count": self.entered_count,
        }


class DeactivateScanTokenResponseDTO(EntranceApiBaseDTO):
    ok: bool
    token: str
    event_id: str
    is_active: bool
    already_inactive: bool

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class MemberInfoDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None
    surname: Optional[str] = None


class ValidateEntryResponseDTO(EntranceApiBaseDTO):
    result: str
    membership: Optional[MemberInfoDTO] = None
    scanned_at: Optional[str] = None
    participants_count: Optional[int] = None
    entered_count: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "result": self.result,
            "membership": self.membership.model_dump() if self.membership else None,
            "scanned_at": self.scanned_at,
        }
        if self.participants_count is not None:
            payload["participants_count"] = self.participants_count
        if self.entered_count is not None:
            payload["entered_count"] = self.entered_count
        return payload


class ManualEntryResponseDTO(EntranceApiBaseDTO):
    result: str
    participants_count: int
    entered_count: int

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)
