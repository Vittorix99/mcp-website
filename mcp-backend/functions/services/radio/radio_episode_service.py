from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from firebase_admin import firestore

from dto.radio.radio_episode_dto import (
    CreateRadioEpisodeRequestDTO,
    RadioEpisodeResponseDTO,
    UpdateRadioEpisodeRequestDTO,
)
from errors.service_errors import ValidationError
from mappers.radio import create_episode_dto_to_model, episode_to_response_dto
from repositories.radio import RadioEpisodeRepository, RadioSeasonRepository
from services.soundcloud import SoundCloudService

_MAX_VIDEO_URLS = 3


class RadioEpisodeService:
    def __init__(
        self,
        episode_repository: Optional[RadioEpisodeRepository] = None,
        season_repository: Optional[RadioSeasonRepository] = None,
        soundcloud_service: Optional[SoundCloudService] = None,
    ):
        self.episode_repository = episode_repository or RadioEpisodeRepository()
        self.season_repository = season_repository or RadioSeasonRepository()
        self.soundcloud_service = soundcloud_service or SoundCloudService()

    def _validate_video_urls(self, video_urls: List[str]) -> None:
        if len(video_urls) > _MAX_VIDEO_URLS:
            raise ValidationError(f"video_urls cannot exceed {_MAX_VIDEO_URLS} items")

    def create(self, dto: CreateRadioEpisodeRequestDTO) -> RadioEpisodeResponseDTO:
        self.season_repository.get_by_id_or_raise(dto.season_id)
        self._validate_video_urls(dto.video_urls)

        sc_data = self.soundcloud_service.resolve_track(dto.soundcloud_url)
        model = create_episode_dto_to_model(dto, sc_data)
        created = self.episode_repository.create_from_model(model)
        return episode_to_response_dto(created)

    def get_all(self, published_only: bool = False) -> List[RadioEpisodeResponseDTO]:
        episodes = self.episode_repository.get_all(published_only=published_only)
        return [episode_to_response_dto(e) for e in episodes]

    def get_by_id(self, episode_id: str) -> RadioEpisodeResponseDTO:
        episode = self.episode_repository.get_by_id_or_raise(episode_id)
        return episode_to_response_dto(episode)

    def get_latest_published(self) -> Optional[RadioEpisodeResponseDTO]:
        episode = self.episode_repository.get_latest_published()
        if episode is None:
            return None
        return episode_to_response_dto(episode)

    def update(self, dto: UpdateRadioEpisodeRequestDTO) -> RadioEpisodeResponseDTO:
        episode = self.episode_repository.get_by_id_or_raise(dto.id)

        changes = dto.changes()
        if "video_urls" in changes and changes["video_urls"] is not None:
            self._validate_video_urls(changes["video_urls"])

        for field_name, value in changes.items():
            setattr(episode, field_name, value)
        episode.updated_at = firestore.SERVER_TIMESTAMP

        updated = self.episode_repository.update_from_model(dto.id, episode)
        return episode_to_response_dto(updated)

    def delete(self, episode_id: str) -> None:
        self.episode_repository.get_by_id_or_raise(episode_id)
        self.episode_repository.delete(episode_id)

    def publish(self, episode_id: str) -> RadioEpisodeResponseDTO:
        episode = self.episode_repository.get_by_id_or_raise(episode_id)
        episode.is_published = True
        episode.published_at = datetime.now(timezone.utc)
        episode.updated_at = firestore.SERVER_TIMESTAMP
        updated = self.episode_repository.update_from_model(episode_id, episode)
        return episode_to_response_dto(updated)

    def unpublish(self, episode_id: str) -> RadioEpisodeResponseDTO:
        episode = self.episode_repository.get_by_id_or_raise(episode_id)
        episode.is_published = False
        episode.published_at = None
        episode.updated_at = firestore.SERVER_TIMESTAMP
        updated = self.episode_repository.update_from_model(episode_id, episode)
        return episode_to_response_dto(updated)
