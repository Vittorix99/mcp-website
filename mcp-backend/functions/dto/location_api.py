from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class GetEventLocationQueryDTO(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True, populate_by_name=True)
    event_id: str = Field(min_length=1)


class UpdateEventLocationRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)
    event_id: str = Field(min_length=1)
    label: str = ""
    maps_url: str = ""
    maps_embed_url: str = ""
    address: str = ""
    message: str = ""


class ToggleLocationPublishedRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)
    event_id: str = Field(min_length=1)
    published: bool


class AdminEventLocationResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)
    label: str = ""
    maps_url: str = ""
    maps_embed_url: str = ""
    address: str = ""
    message: str = ""
    published: bool = False

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump()


class MemberEventLocationResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)
    label: str = ""
    maps_url: str = ""
    maps_embed_url: str = ""
    address: str = ""
    message: str = ""
    hint: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump()
