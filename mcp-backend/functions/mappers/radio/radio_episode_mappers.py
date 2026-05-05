from __future__ import annotations

from typing import Dict

from firebase_admin import firestore

from dto.radio.radio_episode_dto import CreateRadioEpisodeRequestDTO, RadioEpisodeResponseDTO
from models.radio import RadioEpisode
from utils.slug_utils import build_slug


def create_episode_dto_to_model(dto: CreateRadioEpisodeRequestDTO, sc_data: Dict) -> RadioEpisode:
    slug = build_slug(sc_data.get("title", ""), suffix=f"ep-{dto.episode_number}")
    return RadioEpisode(
        slug=slug,
        soundcloud_track_id=sc_data["soundcloud_track_id"],
        title=sc_data["title"],
        soundcloud_url=sc_data["soundcloud_url"],
        soundcloud_artwork_url=sc_data.get("soundcloud_artwork_url"),
        soundcloud_stream_url=sc_data.get("soundcloud_stream_url"),
        soundcloud_waveform_url=sc_data.get("soundcloud_waveform_url"),
        duration=sc_data["duration"],
        access=sc_data["access"],
        genres=sc_data.get("genres", []),
        season_id=dto.season_id,
        episode_number=dto.episode_number,
        description=dto.description,
        artist_ids=dto.artist_ids,
        video_urls=dto.video_urls,
        recorded_at=dto.recorded_at,
        published_at=None,
        is_published=False,
        created_at=firestore.SERVER_TIMESTAMP,
        updated_at=firestore.SERVER_TIMESTAMP,
    )


def episode_to_response_dto(episode: RadioEpisode) -> RadioEpisodeResponseDTO:
    return RadioEpisodeResponseDTO(
        id=episode.id,
        slug=episode.slug or "",
        soundcloud_track_id=episode.soundcloud_track_id,
        title=episode.title,
        soundcloud_url=episode.soundcloud_url,
        soundcloud_artwork_url=episode.soundcloud_artwork_url,
        soundcloud_stream_url=episode.soundcloud_stream_url,
        soundcloud_waveform_url=episode.soundcloud_waveform_url,
        duration=episode.duration,
        access=episode.access,
        season_id=episode.season_id,
        episode_number=episode.episode_number,
        description=episode.description,
        custom_artwork_url=episode.custom_artwork_url,
        artist_ids=episode.artist_ids or [],
        video_urls=episode.video_urls or [],
        genres=episode.genres or [],
        recorded_at=episode.recorded_at,
        published_at=episode.published_at,
        is_published=episode.is_published,
        created_at=episode.created_at,
        updated_at=episode.updated_at,
    )
