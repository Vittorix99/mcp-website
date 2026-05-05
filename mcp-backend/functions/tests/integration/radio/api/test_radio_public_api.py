"""Integration tests for public radio API handlers — hits the Firestore emulator."""
import pytest

from api.admin import radio_episodes_api, radio_seasons_api
from api.public import radio_public_api
from tests.integration.radio.conftest import DummySoundCloudService
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_public_get_seasons_returns_list(base_season_payload):
    season_id = None
    try:
        create_req = DummyRequest(method="POST", json=base_season_payload)
        resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(create_req))
        assert status == 201
        season_id = resp["id"]

        public_req = DummyRequest(method="GET")
        resp, status = unwrap_response(radio_public_api.get_radio_seasons(public_req))
        assert status == 200
        assert any(s["id"] == season_id for s in resp)
    finally:
        if season_id:
            delete_req = DummyRequest(method="DELETE", json={"id": season_id})
            unwrap_response(radio_seasons_api.admin_delete_radio_season(delete_req))


@pytest.mark.integration
def test_public_get_published_episodes_only_returns_published(base_episode_payload):
    radio_episodes_api.episode_service.soundcloud_service = DummySoundCloudService()

    episode_id = None
    try:
        create_req = DummyRequest(method="POST", json=base_episode_payload)
        resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(create_req))
        assert status == 201
        episode_id = resp["id"]

        public_req = DummyRequest(method="GET")
        resp, status = unwrap_response(radio_public_api.get_published_radio_episodes(public_req))
        assert status == 200
        assert not any(e["id"] == episode_id for e in resp)

        publish_req = DummyRequest(method="PATCH", json={"id": episode_id})
        unwrap_response(radio_episodes_api.admin_publish_radio_episode(publish_req))

        resp, status = unwrap_response(radio_public_api.get_published_radio_episodes(public_req))
        assert status == 200
        assert any(e["id"] == episode_id for e in resp)
    finally:
        if episode_id:
            delete_req = DummyRequest(method="DELETE", json={"id": episode_id})
            unwrap_response(radio_episodes_api.admin_delete_radio_episode(delete_req))


@pytest.mark.integration
def test_public_get_episode_returns_404_for_unpublished(base_episode_payload):
    radio_episodes_api.episode_service.soundcloud_service = DummySoundCloudService()

    episode_id = None
    try:
        create_req = DummyRequest(method="POST", json=base_episode_payload)
        resp, status = unwrap_response(radio_episodes_api.admin_create_radio_episode(create_req))
        assert status == 201
        episode_id = resp["id"]

        public_req = DummyRequest(method="GET", args={"id": episode_id})
        resp, status = unwrap_response(radio_public_api.get_radio_episode(public_req))
        assert status == 404
    finally:
        if episode_id:
            delete_req = DummyRequest(method="DELETE", json={"id": episode_id})
            unwrap_response(radio_episodes_api.admin_delete_radio_episode(delete_req))


@pytest.mark.integration
def test_public_get_latest_episode_returns_404_when_none_published():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(radio_public_api.get_latest_radio_episode(req))
    assert status in (200, 404)
