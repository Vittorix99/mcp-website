"""Unit tests for RadioEpisodeService — no Firestore, no real SoundCloud calls."""
import pytest
from firebase_admin import firestore

from dto.radio.radio_episode_dto import CreateRadioEpisodeRequestDTO, UpdateRadioEpisodeRequestDTO
from errors.service_errors import (
    RadioEpisodeNotFoundError,
    RadioSeasonNotFoundError,
    SoundCloudTrackNotFoundError,
    ValidationError,
)
from models.radio import RadioEpisode, RadioSeason
from services.radio.radio_episode_service import RadioEpisodeService


# ---------------------------------------------------------------------------
# Dummy repositories
# ---------------------------------------------------------------------------

class _DummySeasonRepo:
    def __init__(self, seasons=None):
        self._store: dict[str, RadioSeason] = seasons or {}

    def get_by_id_or_raise(self, season_id: str) -> RadioSeason:
        if season_id not in self._store:
            raise RadioSeasonNotFoundError(f"Season not found: {season_id}")
        return self._store[season_id]


class _DummyEpisodeRepo:
    def __init__(self):
        self._store: dict[str, RadioEpisode] = {}
        self._next_id = 1

    def _next(self):
        id_ = f"ep-{self._next_id}"
        self._next_id += 1
        return id_

    def create_from_model(self, episode: RadioEpisode) -> RadioEpisode:
        id_ = self._next()
        episode.id = id_
        self._store[id_] = episode
        return episode

    def get_all(self, published_only: bool = False) -> list:
        episodes = list(self._store.values())
        if published_only:
            return [e for e in episodes if e.is_published]
        return episodes

    def get_by_id_or_raise(self, episode_id: str) -> RadioEpisode:
        if episode_id not in self._store:
            raise RadioEpisodeNotFoundError(f"Not found: {episode_id}")
        return self._store[episode_id]

    def get_latest_published(self):
        published = [e for e in self._store.values() if e.is_published]
        if not published:
            return None
        return sorted(published, key=lambda e: e.published_at or "", reverse=True)[0]

    def update_from_model(self, episode_id: str, episode: RadioEpisode) -> RadioEpisode:
        self._store[episode_id] = episode
        return episode

    def delete(self, episode_id: str) -> None:
        self._store.pop(episode_id, None)


# ---------------------------------------------------------------------------
# Dummy SoundCloud service
# ---------------------------------------------------------------------------

_DEFAULT_SC_DATA = {
    "soundcloud_track_id": "99999",
    "title": "Mocked Track",
    "soundcloud_url": "https://soundcloud.com/artist/mocked",
    "soundcloud_artwork_url": "https://art.jpg",
    "soundcloud_stream_url": "https://stream.url",
    "soundcloud_waveform_url": "https://wave.url",
    "duration": 180000,
    "access": "playable",
    "genres": ["Techno"],
}


class _DummySoundCloudService:
    def __init__(self, sc_data=None, raise_error=None):
        self._sc_data = sc_data or _DEFAULT_SC_DATA
        self._raise = raise_error

    def resolve_track(self, url: str) -> dict:
        if self._raise:
            raise self._raise
        return self._sc_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEASON_ID = "season-1"
_VALID_SEASON = RadioSeason(id=_SEASON_ID, name="Test Season", year=2026)


def _make_service(seasons=None, sc_service=None):
    svc = RadioEpisodeService()
    svc.season_repository = _DummySeasonRepo(
        {_SEASON_ID: _VALID_SEASON} if seasons is None else seasons
    )
    svc.episode_repository = _DummyEpisodeRepo()
    svc.soundcloud_service = sc_service or _DummySoundCloudService()
    return svc


def _base_create_payload(**overrides):
    payload = {
        "soundcloudUrl": "https://soundcloud.com/artist/track",
        "seasonId": _SEASON_ID,
        "episodeNumber": 1,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_episode_happy_path():
    svc = _make_service()
    dto = CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload())

    result = svc.create(dto)

    assert result.id == "ep-1"
    assert result.title == "Mocked Track"
    assert result.soundcloud_track_id == "99999"
    assert result.is_published is False
    assert result.genres == ["Techno"]
    assert result.season_id == _SEASON_ID


def test_create_episode_fills_soundcloud_metadata():
    svc = _make_service()
    dto = CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload())

    result = svc.create(dto)

    assert result.soundcloud_artwork_url == "https://art.jpg"
    assert result.soundcloud_stream_url == "https://stream.url"
    assert result.duration == 180000


def test_create_episode_rejects_unknown_season():
    svc = _make_service(seasons={})
    dto = CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload())

    with pytest.raises(RadioSeasonNotFoundError):
        svc.create(dto)


def test_create_episode_rejects_too_many_video_urls():
    svc = _make_service()
    dto = CreateRadioEpisodeRequestDTO.model_validate(
        _base_create_payload(videoUrls=["u1", "u2", "u3", "u4"])
    )

    with pytest.raises(ValidationError):
        svc.create(dto)


def test_create_episode_propagates_soundcloud_not_found():
    svc = _make_service(sc_service=_DummySoundCloudService(raise_error=SoundCloudTrackNotFoundError("not found")))
    dto = CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload())

    with pytest.raises(SoundCloudTrackNotFoundError):
        svc.create(dto)


def test_create_episode_stores_editorial_fields():
    svc = _make_service()
    dto = CreateRadioEpisodeRequestDTO.model_validate(
        _base_create_payload(episodeNumber=3, description="A great episode", artistIds=["artist-1"])
    )

    result = svc.create(dto)

    assert result.episode_number == 3
    assert result.description == "A great episode"
    assert result.artist_ids == ["artist-1"]


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------

def test_get_all_returns_all_episodes():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload(episodeNumber=1)))
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload(episodeNumber=2)))

    result = svc.get_all()

    assert len(result) == 2


def test_get_all_published_only_filters_correctly():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload(episodeNumber=1)))
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload(episodeNumber=2)))
    svc.publish("ep-1")

    result = svc.get_all(published_only=True)

    assert len(result) == 1
    assert result[0].id == "ep-1"


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_happy_path():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))

    result = svc.get_by_id("ep-1")

    assert result.id == "ep-1"


def test_get_by_id_raises_not_found():
    svc = _make_service()
    with pytest.raises(RadioEpisodeNotFoundError):
        svc.get_by_id("ghost")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_episode_description():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))

    dto = UpdateRadioEpisodeRequestDTO.model_validate({"id": "ep-1", "description": "Updated"})
    result = svc.update(dto)

    assert result.description == "Updated"
    assert result.updated_at == firestore.SERVER_TIMESTAMP


def test_update_episode_does_not_change_soundcloud_fields():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))

    dto = UpdateRadioEpisodeRequestDTO.model_validate({"id": "ep-1", "description": "New desc"})
    result = svc.update(dto)

    assert result.title == "Mocked Track"
    assert result.soundcloud_track_id == "99999"


def test_update_episode_rejects_too_many_video_urls():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))

    dto = UpdateRadioEpisodeRequestDTO.model_validate(
        {"id": "ep-1", "videoUrls": ["a", "b", "c", "d"]}
    )
    with pytest.raises(ValidationError):
        svc.update(dto)


def test_update_episode_not_found():
    svc = _make_service()
    with pytest.raises(RadioEpisodeNotFoundError):
        svc.update(UpdateRadioEpisodeRequestDTO.model_validate({"id": "ghost", "description": "X"}))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_episode_happy_path():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))
    svc.delete("ep-1")

    assert svc.episode_repository.get_all() == []


def test_delete_episode_not_found():
    svc = _make_service()
    with pytest.raises(RadioEpisodeNotFoundError):
        svc.delete("ghost")


# ---------------------------------------------------------------------------
# publish / unpublish
# ---------------------------------------------------------------------------

def test_publish_sets_is_published_true():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))

    result = svc.publish("ep-1")

    assert result.is_published is True
    assert result.published_at is not None


def test_unpublish_clears_published_at():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))
    svc.publish("ep-1")

    result = svc.unpublish("ep-1")

    assert result.is_published is False
    assert result.published_at is None


def test_publish_episode_not_found():
    svc = _make_service()
    with pytest.raises(RadioEpisodeNotFoundError):
        svc.publish("ghost")


def test_unpublish_episode_not_found():
    svc = _make_service()
    with pytest.raises(RadioEpisodeNotFoundError):
        svc.unpublish("ghost")


# ---------------------------------------------------------------------------
# get_latest_published
# ---------------------------------------------------------------------------

def test_get_latest_published_returns_none_when_none_published():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))

    result = svc.get_latest_published()

    assert result is None


def test_get_latest_published_returns_published_episode():
    svc = _make_service()
    svc.create(CreateRadioEpisodeRequestDTO.model_validate(_base_create_payload()))
    svc.publish("ep-1")

    result = svc.get_latest_published()

    assert result is not None
    assert result.is_published is True
