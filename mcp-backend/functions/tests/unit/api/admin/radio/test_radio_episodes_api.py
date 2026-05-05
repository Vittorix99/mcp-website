"""Unit tests for admin radio episodes API handlers."""
import types

import pytest

from api.admin import radio_episodes_api
from dto.radio.radio_episode_dto import RadioEpisodeResponseDTO
from errors.service_errors import (
    RadioEpisodeNotFoundError,
    RadioSeasonNotFoundError,
    SoundCloudAPIError,
    SoundCloudTrackNotFoundError,
    SoundCloudTrackNotPlayableError,
    ValidationError,
)
from tests.utils import DummyRequest, unwrap_response


def _episode_dto(**kwargs):
    defaults = dict(
        id="ep-1",
        soundcloud_track_id="999",
        title="Test Track",
        soundcloud_url="https://soundcloud.com/t",
        duration=180000,
        access="playable",
        season_id="s1",
        episode_number=1,
        is_published=False,
        artist_ids=[],
        video_urls=[],
        genres=[],
    )
    defaults.update(kwargs)
    return RadioEpisodeResponseDTO(**defaults)


def _base_create_json(**overrides):
    payload = {
        "soundcloudUrl": "https://soundcloud.com/artist/track",
        "seasonId": "s1",
        "episodeNumber": 1,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# GET /admin/radio/episodes (list)
# ---------------------------------------------------------------------------

def test_get_episodes_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(get_all=lambda published_only: [_episode_dto()]),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episodes(req))

    assert status == 200
    assert isinstance(resp, list)
    assert resp[0]["id"] == "ep-1"


# ---------------------------------------------------------------------------
# POST /admin/radio/episodes (create)
# ---------------------------------------------------------------------------

def test_create_episode_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(create=lambda dto: _episode_dto()),
    )
    req = DummyRequest(method="POST", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 201
    assert resp["id"] == "ep-1"


def test_create_episode_missing_body():
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_create_episode_missing_soundcloud_url():
    req = DummyRequest(method="POST", json={"seasonId": "s1", "episodeNumber": 1})
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 400


def test_create_episode_soundcloud_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            create=lambda dto: (_ for _ in ()).throw(SoundCloudTrackNotFoundError("not found"))
        ),
    )
    req = DummyRequest(method="POST", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 404


def test_create_episode_soundcloud_not_playable(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            create=lambda dto: (_ for _ in ()).throw(SoundCloudTrackNotPlayableError("blocked"))
        ),
    )
    req = DummyRequest(method="POST", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 400


def test_create_episode_soundcloud_api_error(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            create=lambda dto: (_ for _ in ()).throw(SoundCloudAPIError("timeout"))
        ),
    )
    req = DummyRequest(method="POST", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 502


def test_create_episode_season_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            create=lambda dto: (_ for _ in ()).throw(RadioSeasonNotFoundError("no season"))
        ),
    )
    req = DummyRequest(method="POST", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 404


def test_create_episode_too_many_video_urls(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            create=lambda dto: (_ for _ in ()).throw(ValidationError("video_urls max 3"))
        ),
    )
    req = DummyRequest(method="POST", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 400


def test_create_episode_wrong_method():
    req = DummyRequest(method="GET", json=_base_create_json())
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))

    assert status == 405


# ---------------------------------------------------------------------------
# GET /admin/radio/episodes?id=xxx
# ---------------------------------------------------------------------------

def test_get_episode_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(get_by_id=lambda id_: _episode_dto(id=id_)),
    )
    req = DummyRequest(method="GET", args={"id": "ep-1"})
    resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episode(req))

    assert status == 200
    assert resp["id"] == "ep-1"


def test_get_episode_missing_id():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episode(req))

    assert status == 400


def test_get_episode_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            get_by_id=lambda id_: (_ for _ in ()).throw(RadioEpisodeNotFoundError("gone"))
        ),
    )
    req = DummyRequest(method="GET", args={"id": "ghost"})
    resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episode(req))

    assert status == 404


# ---------------------------------------------------------------------------
# PUT /admin/radio/episodes (update)
# ---------------------------------------------------------------------------

def test_update_episode_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(update=lambda dto: _episode_dto(id=dto.id)),
    )
    req = DummyRequest(method="PUT", json={"id": "ep-1", "description": "New"})
    resp, status = unwrap_response(radio_episodes_api.admin_update_radio_episode(req))

    assert status == 200


def test_update_episode_missing_id():
    req = DummyRequest(method="PUT", json={"description": "No ID"})
    resp, status = unwrap_response(radio_episodes_api.admin_update_radio_episode(req))

    assert status == 400


# ---------------------------------------------------------------------------
# DELETE /admin/radio/episodes
# ---------------------------------------------------------------------------

def test_delete_episode_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(delete=lambda id_: None),
    )
    req = DummyRequest(method="DELETE", json={"id": "ep-1"})
    resp, status = unwrap_response(radio_episodes_api.admin_delete_radio_episode(req))

    assert status == 200
    assert resp["message"] == "Radio episode deleted"


def test_delete_episode_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(radio_episodes_api.admin_delete_radio_episode(req))

    assert status == 400


# ---------------------------------------------------------------------------
# PATCH publish / unpublish
# ---------------------------------------------------------------------------

def test_publish_episode_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(publish=lambda id_: _episode_dto(id=id_, is_published=True)),
    )
    req = DummyRequest(method="PATCH", json={"id": "ep-1"})
    resp, status = unwrap_response(radio_episodes_api.admin_publish_radio_episode(req))

    assert status == 200
    assert resp["isPublished"] is True


def test_unpublish_episode_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(unpublish=lambda id_: _episode_dto(id=id_, is_published=False)),
    )
    req = DummyRequest(method="PATCH", json={"id": "ep-1"})
    resp, status = unwrap_response(radio_episodes_api.admin_unpublish_radio_episode(req))

    assert status == 200
    assert resp["isPublished"] is False


def test_publish_episode_missing_id():
    req = DummyRequest(method="PATCH", json={})
    resp, status = unwrap_response(radio_episodes_api.admin_publish_radio_episode(req))

    assert status == 400


def test_publish_episode_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_episodes_api,
        "episode_service",
        types.SimpleNamespace(
            publish=lambda id_: (_ for _ in ()).throw(RadioEpisodeNotFoundError("gone"))
        ),
    )
    req = DummyRequest(method="PATCH", json={"id": "ghost"})
    resp, status = unwrap_response(radio_episodes_api.admin_publish_radio_episode(req))

    assert status == 404
