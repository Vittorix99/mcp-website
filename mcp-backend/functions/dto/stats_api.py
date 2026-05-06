from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StatsApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class EventSnapshotQueryDTO(StatsApiBaseDTO):
    event_id: str = Field(min_length=1)


class EntranceFlowQueryDTO(StatsApiBaseDTO):
    event_id: str = Field(min_length=1)


class RebuildAnalyticsRequestDTO(StatsApiBaseDTO):
    scope: str = "all"
    event_id: Optional[str] = None

    @field_validator("scope", mode="before")
    @classmethod
    def normalize_scope(cls, value):
        return str(value or "all").strip().lower()

    @field_validator("event_id", mode="before")
    @classmethod
    def normalize_event_id(cls, value):
        if value is None:
            return None
        raw = str(value).strip()
        return raw or None

    @model_validator(mode="after")
    def validate_scope(self) -> "RebuildAnalyticsRequestDTO":
        if self.scope not in {"event", "global", "all"}:
            raise ValueError("scope must be event|global|all")
        if self.scope == "event" and not self.event_id:
            raise ValueError("event_id is required when scope=event")
        return self
