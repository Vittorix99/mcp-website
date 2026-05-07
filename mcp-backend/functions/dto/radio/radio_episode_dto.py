from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RadioEpisodeBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class CreateRadioEpisodeRequestDTO(RadioEpisodeBaseDTO):
    soundcloud_url: str = Field(min_length=1, alias="soundcloudUrl")
    season_id: str = Field(min_length=1, alias="seasonId")
    episode_number: int = Field(gt=0, alias="episodeNumber")
    description: Optional[str] = None
    custom_artwork_url: Optional[str] = Field(default=None, alias="customArtworkUrl")
    artist_ids: List[str] = Field(default_factory=list, alias="artistIds")
    video_urls: List[str] = Field(default_factory=list, alias="videoUrls")
    recorded_at: Optional[datetime] = Field(default=None, alias="recordedAt")

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class UpdateRadioEpisodeRequestDTO(RadioEpisodeBaseDTO):
    id: str = Field(min_length=1)
    season_id: Optional[str] = Field(default=None, alias="seasonId")
    episode_number: Optional[int] = Field(default=None, alias="episodeNumber")
    description: Optional[str] = None
    custom_artwork_url: Optional[str] = Field(default=None, alias="customArtworkUrl")
    artist_ids: Optional[List[str]] = Field(default=None, alias="artistIds")
    video_urls: Optional[List[str]] = Field(default=None, alias="videoUrls")
    recorded_at: Optional[datetime] = Field(default=None, alias="recordedAt")

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    def changes(self) -> Dict[str, Any]:
        allowed: Set[str] = set(self.model_fields_set) - {"id"}
        return {f: getattr(self, f) for f in allowed}


class RadioEpisodeIdRequestDTO(RadioEpisodeBaseDTO):
    id: str = Field(min_length=1)


class RadioEpisodeResponseDTO(RadioEpisodeBaseDTO):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    id: Optional[str] = None
    slug: str = ""
    soundcloud_track_id: str = Field(serialization_alias="soundcloudTrackId")
    title: str
    soundcloud_url: str = Field(serialization_alias="soundcloudUrl")
    soundcloud_artwork_url: Optional[str] = Field(default=None, serialization_alias="soundcloudArtworkUrl")
    soundcloud_stream_url: Optional[str] = Field(default=None, serialization_alias="soundcloudStreamUrl")
    soundcloud_waveform_url: Optional[str] = Field(default=None, serialization_alias="soundcloudWaveformUrl")
    duration: int
    access: str
    season_id: str = Field(serialization_alias="seasonId")
    episode_number: int = Field(serialization_alias="episodeNumber")
    description: Optional[str] = None
    custom_artwork_url: Optional[str] = Field(default=None, serialization_alias="customArtworkUrl")
    artist_ids: List[str] = Field(default_factory=list, serialization_alias="artistIds")
    video_urls: List[str] = Field(default_factory=list, serialization_alias="videoUrls")
    genres: List[str] = Field(default_factory=list)
    recorded_at: Optional[Any] = Field(default=None, serialization_alias="recordedAt")
    published_at: Optional[Any] = Field(default=None, serialization_alias="publishedAt")
    is_published: bool = Field(serialization_alias="isPublished")
    created_at: Optional[Any] = Field(default=None, serialization_alias="createdAt")
    updated_at: Optional[Any] = Field(default=None, serialization_alias="updatedAt")

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
