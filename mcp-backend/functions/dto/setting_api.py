from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SettingApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── Request DTOs ──────────────────────────────────────────────────────────────

class GetSettingQueryDTO(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, str_strip_whitespace=True)
    key: Optional[str] = None


class SetSettingRequestDTO(SettingApiBaseDTO):
    key: str = Field(min_length=1)
    value: Any


# ── Response DTOs ─────────────────────────────────────────────────────────────

class SettingResponseDTO(SettingApiBaseDTO):
    key: str
    value: Any

    def to_payload(self) -> Dict[str, Any]:
        return {"key": self.key, "value": self.value}


class SettingsListResponseDTO(SettingApiBaseDTO):
    settings: List[SettingResponseDTO]

    def to_payload(self) -> Dict[str, Any]:
        return {"settings": [s.to_payload() for s in self.settings]}


class SetSettingResponseDTO(SettingApiBaseDTO):
    message: str
    setting: SettingResponseDTO

    def to_payload(self) -> Dict[str, Any]:
        return {"message": self.message, "setting": self.setting.to_payload()}
