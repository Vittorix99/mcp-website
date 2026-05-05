"""Integration tests for RadioEpisodeService — hits the Firestore emulator.

SoundCloud calls are replaced by DummySoundCloudService from conftest.
"""
import pytest

from dto.radio.radio_episode_dto import CreateRadioEpisodeRequestDTO, UpdateRadioEpisodeRequestDTO
from errors.service_errors import RadioEpisodeNotFoundError, ValidationError


@pytest.mark.integration
def test_episode_crud(episode_service, episode_dto, season_service, created_season):
    """Full create → get → update → publish → unpublish → delete lifecycle."""
    episode_id = None
    try:
        created = episode_service.create(episode_dto)
        episode_id = created.id
        assert episode_id
        assert created.title == "Integration Test Track"
        assert created.season_id == created_season.id
        assert created.is_published is False
        assert created.genres == ["House"]

        fetched = episode_service.get_by_id(episode_id)
        assert fetched.id == episode_id

        update_dto = UpdateRadioEpisodeRequestDTO.model_validate(
            {"id": episode_id, "description": "Updated description"}
        )
        updated = episode_service.update(update_dto)
        assert updated.description == "Updated description"
        assert updated.title == "Integration Test Track"

        published = episode_service.publish(episode_id)
        assert published.is_published is True
        assert published.published_at is not None

        unpublished = episode_service.unpublish(episode_id)
        assert unpublished.is_published is False
        assert unpublished.published_at is None

        episode_service.delete(episode_id)
        episode_id = None

        with pytest.raises(RadioEpisodeNotFoundError):
            episode_service.get_by_id(episode_id or "deleted")
    finally:
        if episode_id:
            episode_service.delete(episode_id)


@pytest.mark.integration
def test_get_all_published_only(episode_service, episode_dto):
    ep1_id = ep2_id = None
    try:
        ep1 = episode_service.create(episode_dto)
        ep1_id = ep1.id

        from uuid import uuid4
        from dto.radio.radio_episode_dto import CreateRadioEpisodeRequestDTO
        ep2_payload = {
            "soundcloudUrl": f"https://soundcloud.com/artist/ep2-{uuid4().hex[:6]}",
            "seasonId": episode_dto.season_id,
            "episodeNumber": 2,
        }
        ep2 = episode_service.create(CreateRadioEpisodeRequestDTO.model_validate(ep2_payload))
        ep2_id = ep2.id

        episode_service.publish(ep1_id)

        published = episode_service.get_all(published_only=True)
        published_ids = {e.id for e in published}
        assert ep1_id in published_ids
        assert ep2_id not in published_ids
    finally:
        for ep_id in [ep1_id, ep2_id]:
            if ep_id:
                try:
                    episode_service.delete(ep_id)
                except Exception:
                    pass


@pytest.mark.integration
def test_get_latest_published(episode_service, episode_dto):
    episode_id = None
    try:
        created = episode_service.create(episode_dto)
        episode_id = created.id
        episode_service.publish(episode_id)

        latest = episode_service.get_latest_published()
        assert latest is not None
        assert latest.is_published is True
    finally:
        if episode_id:
            episode_service.delete(episode_id)


@pytest.mark.integration
def test_create_episode_rejects_too_many_video_urls(episode_service, episode_dto):
    dto = CreateRadioEpisodeRequestDTO.model_validate(
        {
            "soundcloudUrl": episode_dto.soundcloud_url,
            "seasonId": episode_dto.season_id,
            "episodeNumber": 99,
            "videoUrls": ["u1", "u2", "u3", "u4"],
        }
    )
    with pytest.raises(ValidationError):
        episode_service.create(dto)


@pytest.mark.integration
def test_update_episode_rejects_too_many_video_urls(episode_service, episode_dto):
    episode_id = None
    try:
        created = episode_service.create(episode_dto)
        episode_id = created.id

        dto = UpdateRadioEpisodeRequestDTO.model_validate(
            {"id": episode_id, "videoUrls": ["a", "b", "c", "d"]}
        )
        with pytest.raises(ValidationError):
            episode_service.update(dto)
    finally:
        if episode_id:
            episode_service.delete(episode_id)


@pytest.mark.integration
def test_get_by_id_not_found(episode_service):
    with pytest.raises(RadioEpisodeNotFoundError):
        episode_service.get_by_id("nonexistent-episode-id")


@pytest.mark.integration
def test_delete_not_found(episode_service):
    with pytest.raises(RadioEpisodeNotFoundError):
        episode_service.delete("nonexistent-episode-id")
