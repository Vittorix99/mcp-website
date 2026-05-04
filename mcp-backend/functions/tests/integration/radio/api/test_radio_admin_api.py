"""Integration tests for admin radio API handlers — hits the Firestore emulator."""
import pytest

from api.admin import radio_episodes_api, radio_seasons_api
from tests.integration.radio.conftest import DummySoundCloudService
from tests.utils import DummyRequest, unwrap_response


# ---------------------------------------------------------------------------
# Seasons admin API
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_admin_seasons_crud_api(base_season_payload):
    """Full CRUD cycle through the seasons API handler layer."""
    season_id = None
    try:
        create_req = DummyRequest(method="POST", json=base_season_payload)
        resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(create_req))
        assert status == 201
        season_id = resp.get("id")
        assert season_id
        assert resp["name"] == base_season_payload["name"]

        get_req = DummyRequest(method="GET", args={"id": season_id})
        resp, status = unwrap_response(radio_seasons_api.admin_get_radio_season(get_req))
        assert status == 200
        assert resp["id"] == season_id

        update_req = DummyRequest(method="PUT", json={"id": season_id, "name": "API Updated"})
        resp, status = unwrap_response(radio_seasons_api.admin_update_radio_season(update_req))
        assert status == 200
        assert resp["name"] == "API Updated"

        list_req = DummyRequest(method="GET")
        resp, status = unwrap_response(radio_seasons_api.admin_get_radio_seasons(list_req))
        assert status == 200
        assert any(s["id"] == season_id for s in resp)
    finally:
        if season_id:
            delete_req = DummyRequest(method="DELETE", json={"id": season_id})
            unwrap_response(radio_seasons_api.admin_delete_radio_season(delete_req))


@pytest.mark.integration
def test_admin_get_season_not_found():
    req = DummyRequest(method="GET", args={"id": "nonexistent-season"})
    resp, status = unwrap_response(radio_seasons_api.admin_get_radio_season(req))
    assert status == 404


@pytest.mark.integration
def test_admin_create_season_invalid_payload():
    req = DummyRequest(method="POST", json={"name": ""})
    resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(req))
    assert status == 400


# ---------------------------------------------------------------------------
# Episodes admin API
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_admin_episodes_crud_api(base_episode_payload):
    """Full CRUD + publish/unpublish cycle through the episodes API handler layer."""
    episode_id = None

    radio_episodes_api.episode_service.soundcloud_service = DummySoundCloudService()

    try:
        create_req = DummyRequest(method="POST", json=base_episode_payload)
        resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(create_req))
        assert status == 201
        episode_id = resp.get("id")
        assert episode_id
        assert resp["title"] == "Integration Test Track"
        assert resp["isPublished"] is False

        get_req = DummyRequest(method="GET", args={"id": episode_id})
        resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episode(get_req))
        assert status == 200
        assert resp["id"] == episode_id

        update_req = DummyRequest(
            method="PUT",
            json={"id": episode_id, "description": "API Updated description"},
        )
        resp, status = unwrap_response(radio_episodes_api.admin_update_radio_episode(update_req))
        assert status == 200

        publish_req = DummyRequest(method="PATCH", json={"id": episode_id})
        resp, status = unwrap_response(radio_episodes_api.admin_publish_radio_episode(publish_req))
        assert status == 200
        assert resp["isPublished"] is True

        unpublish_req = DummyRequest(method="PATCH", json={"id": episode_id})
        resp, status = unwrap_response(radio_episodes_api.admin_unpublish_radio_episode(unpublish_req))
        assert status == 200
        assert resp["isPublished"] is False

        list_req = DummyRequest(method="GET")
        resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episodes(list_req))
        assert status == 200
        assert any(e["id"] == episode_id for e in resp)
    finally:
        if episode_id:
            delete_req = DummyRequest(method="DELETE", json={"id": episode_id})
            unwrap_response(radio_episodes_api.admin_delete_radio_episode(delete_req))


@pytest.mark.integration
def test_admin_get_episode_not_found():
    req = DummyRequest(method="GET", args={"id": "nonexistent-episode"})
    resp, status = unwrap_response(radio_episodes_api.admin_get_radio_episode(req))
    assert status == 404


@pytest.mark.integration
def test_admin_create_episode_missing_soundcloud_url(base_episode_payload):
    payload = dict(base_episode_payload)
    payload.pop("soundcloudUrl", None)
    req = DummyRequest(method="POST", json=payload)
    resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(req))
    assert status == 400


@pytest.mark.integration
def test_admin_publish_episode_not_found():
    req = DummyRequest(method="PATCH", json={"id": "nonexistent-episode"})
    resp, status = unwrap_response(radio_episodes_api.admin_publish_radio_episode(req))
    assert status == 404
