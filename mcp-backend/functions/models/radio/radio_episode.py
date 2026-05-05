from dataclasses import dataclass, field
from typing import Any, List, Optional

from models.base import FirestoreModel


@dataclass
class RadioEpisode(FirestoreModel):
    """Represents a radio episode document in the ``radio_episodes`` collection."""

    slug: str = ""
    soundcloud_track_id: str = field(default="", metadata={"firestore_name": "soundcloudTrackId"})
    title: str = ""
    soundcloud_url: str = field(default="", metadata={"firestore_name": "soundcloudUrl"})
    soundcloud_artwork_url: Optional[str] = field(default=None, metadata={"firestore_name": "soundcloudArtworkUrl"})
    soundcloud_stream_url: Optional[str] = field(default=None, metadata={"firestore_name": "soundcloudStreamUrl"})
    soundcloud_waveform_url: Optional[str] = field(default=None, metadata={"firestore_name": "soundcloudWaveformUrl"})
    duration: int = 0
    access: str = ""
    season_id: str = field(default="", metadata={"firestore_name": "seasonId"})
    episode_number: int = field(default=0, metadata={"firestore_name": "episodeNumber"})
    description: Optional[str] = None
    artist_ids: List[str] = field(default_factory=list, metadata={"firestore_name": "artistIds"})
    custom_artwork_url: Optional[str] = field(default=None, metadata={"firestore_name": "customArtworkUrl"})
    video_urls: List[str] = field(default_factory=list, metadata={"firestore_name": "videoUrls"})
    genres: List[str] = field(default_factory=list)
    recorded_at: Optional[Any] = field(default=None, metadata={"firestore_name": "recordedAt"})
    published_at: Optional[Any] = field(default=None, metadata={"firestore_name": "publishedAt"})
    is_published: bool = field(default=False, metadata={"firestore_name": "isPublished"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})
    updated_at: Optional[Any] = field(default=None, metadata={"firestore_name": "updatedAt"})
