from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from google.cloud.firestore_v1 import FieldFilter

from errors.service_errors import RadioEpisodeNotFoundError
from models.radio import RadioEpisode
from repositories.base import BaseRepository


class RadioEpisodeRepository(BaseRepository[RadioEpisode]):
    def __init__(self):
        super().__init__("radio_episodes", RadioEpisode)

    def create_from_model(self, episode: RadioEpisode) -> RadioEpisode:
        doc_id = self.create(episode)
        return self.get_by_id_or_raise(doc_id)

    def get_all(self, published_only: bool = False) -> List[RadioEpisode]:
        if not published_only:
            return super().get_all()
        snapshots = (
            self.collection.where(filter=FieldFilter("isPublished", "==", True))
            .stream()
        )
        return [self._model_from_snapshot(snap) for snap in snapshots]

    def get_by_id_or_raise(self, episode_id: str) -> RadioEpisode:
        episode = self.get_by_id(episode_id)
        if episode is None:
            raise RadioEpisodeNotFoundError(f"Radio episode '{episode_id}' not found")
        return episode

    def get_by_slug(self, slug: str) -> Optional[RadioEpisode]:
        snapshots = (
            self.collection.where(filter=FieldFilter("slug", "==", slug))
            .limit(1)
            .stream()
        )
        results = list(snapshots)
        return self._model_from_snapshot(results[0]) if results else None

    def get_latest_published(self) -> Optional[RadioEpisode]:
        snapshots = (
            self.collection.where(filter=FieldFilter("isPublished", "==", True))
            .stream()
        )
        episodes = [self._model_from_snapshot(snap) for snap in snapshots]
        if not episodes:
            return None

        def published_sort_key(episode: RadioEpisode) -> float:
            published_at = episode.published_at
            if hasattr(published_at, "timestamp"):
                return float(published_at.timestamp())
            if isinstance(published_at, str):
                try:
                    return datetime.fromisoformat(published_at.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    return 0.0
            return 0.0

        return max(episodes, key=published_sort_key)

    def get_by_season(self, season_id: str, published_only: bool = False) -> List[RadioEpisode]:
        query = self.collection.where(filter=FieldFilter("seasonId", "==", season_id))
        if published_only:
            query = query.where(filter=FieldFilter("isPublished", "==", True))
        return [self._model_from_snapshot(snap) for snap in query.stream()]

    def update_from_model(self, episode_id: str, episode: RadioEpisode) -> RadioEpisode:
        self.update(episode_id, episode)
        return self.get_by_id_or_raise(episode_id)

    def delete(self, episode_id: str) -> None:
        self.collection.document(episode_id).delete()
