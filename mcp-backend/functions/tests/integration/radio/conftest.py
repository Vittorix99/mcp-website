"""Fixtures shared by Radio integration tests."""
from uuid import uuid4

import pytest

from dto.radio.radio_episode_dto import CreateRadioEpisodeRequestDTO
from dto.radio.radio_season_dto import CreateRadioSeasonRequestDTO
from models.radio import RadioEpisode, RadioSeason
from repositories.radio import RadioEpisodeRepository, RadioSeasonRepository
from services.radio.radio_episode_service import RadioEpisodeService
from services.radio.radio_season_service import RadioSeasonService


# ---------------------------------------------------------------------------
# Dummy SoundCloud service — avoids hitting the real API in integration tests
# ---------------------------------------------------------------------------

class DummySoundCloudService:
    """Returns predictable data so integration tests don't depend on SoundCloud."""

    def resolve_track(self, url: str) -> dict:
        return {
            "soundcloud_track_id": "integration-track-id",
            "title": "Integration Test Track",
            "soundcloud_url": url,
            "soundcloud_artwork_url": "https://art.jpg",
            "soundcloud_stream_url": "https://stream.url",
            "soundcloud_waveform_url": "https://wave.url",
            "duration": 200000,
            "access": "playable",
            "genres": ["House"],
        }


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

@pytest.fixture
def season_repository():
    return RadioSeasonRepository()


@pytest.fixture
def episode_repository():
    return RadioEpisodeRepository()


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

@pytest.fixture
def season_service():
    return RadioSeasonService()


@pytest.fixture
def episode_service():
    svc = RadioEpisodeService()
    svc.soundcloud_service = DummySoundCloudService()
    return svc


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def base_season_payload():
    suffix = uuid4().hex[:6]
    return {"name": f"Integration Season {suffix}", "year": 2026}


@pytest.fixture
def season_dto(base_season_payload):
    return CreateRadioSeasonRequestDTO.model_validate(base_season_payload)


@pytest.fixture
def created_season(season_service, season_dto):
    """Creates a season and deletes it after the test."""
    result = season_service.create(season_dto)
    yield result
    try:
        season_service.delete(result.id)
    except Exception:
        pass


@pytest.fixture
def base_episode_payload(created_season):
    suffix = uuid4().hex[:6]
    return {
        "soundcloudUrl": f"https://soundcloud.com/artist/track-{suffix}",
        "seasonId": created_season.id,
        "episodeNumber": 1,
        "description": "Integration test episode",
    }


@pytest.fixture
def episode_dto(base_episode_payload):
    return CreateRadioEpisodeRequestDTO.model_validate(base_episode_payload)
