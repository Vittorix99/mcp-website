from __future__ import annotations

from typing import Any, Dict, Optional, Set

from pydantic import BaseModel, ConfigDict, Field


class RadioSeasonBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class CreateRadioSeasonRequestDTO(RadioSeasonBaseDTO):
    name: str = Field(min_length=1)
    year: int
    description: Optional[str] = None


class UpdateRadioSeasonRequestDTO(RadioSeasonBaseDTO):
    id: str = Field(min_length=1)
    name: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None

    def changes(self) -> Dict[str, Any]:
        allowed: Set[str] = set(self.model_fields_set) - {"id"}
        return {f: getattr(self, f) for f in allowed}


class RadioSeasonResponseDTO(RadioSeasonBaseDTO):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    id: Optional[str] = None
    name: str
    year: int
    description: Optional[str] = None
    created_at: Optional[Any] = Field(default=None, serialization_alias="createdAt")
    updated_at: Optional[Any] = Field(default=None, serialization_alias="updatedAt")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
