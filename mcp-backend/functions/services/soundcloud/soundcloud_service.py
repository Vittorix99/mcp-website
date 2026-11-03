from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import requests

from config.external_services import SOUNDCLOUD_CLIENT_ID, SOUNDCLOUD_CLIENT_SECRET
from config.firebase_config import db
from errors.service_errors import (
    SoundCloudAPIError,
    SoundCloudAuthError,
    SoundCloudTrackNotFoundError,
    SoundCloudTrackNotPlayableError,
)
from config.runtime_settings import ProviderMode, RuntimeConfigurationError, get_runtime_settings

_TOKEN_DOC = "soundcloud_token"
_SETTINGS_COLLECTION = "settings"
_TOKEN_GRACE_SECONDS = 300  # refresh 5 min before expiry


class SoundCloudService:
    def __init__(self, client_id=None, client_secret=None):
        self._client_id = client_id
        self._client_secret = client_secret

    def get_token(self) -> str:
        token_ref = db.collection(_SETTINGS_COLLECTION).document(_TOKEN_DOC)
        doc = token_ref.get()

        if doc.exists:
            data = doc.to_dict() or {}
            access_token: Optional[str] = data.get("access_token")
            expires_at = data.get("expires_at")
            if access_token and expires_at:
                now = datetime.now(timezone.utc)
                # expires_at from Firestore is timezone-aware DatetimeWithNanoseconds
                deadline = expires_at - timedelta(seconds=_TOKEN_GRACE_SECONDS)
                if hasattr(deadline, "tzinfo") and deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                if now < deadline:
                    return access_token

        return self._refresh_token(token_ref)

    def _refresh_token(self, token_ref) -> str:
        client_id = self._client_id or SOUNDCLOUD_CLIENT_ID
        client_secret = self._client_secret or SOUNDCLOUD_CLIENT_SECRET
        if not client_id or not client_secret:
            raise SoundCloudAuthError("SoundCloud credentials not configured")

        credentials = base64.b64encode(
            f"{client_id}:{client_secret}".encode()
        ).decode()

        try:
            resp = requests.post(
                "https://secure.soundcloud.com/oauth/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SoundCloudAuthError(f"SoundCloud token request failed: {exc}") from exc

        if not resp.ok:
            raise SoundCloudAuthError(
                f"SoundCloud token endpoint returned {resp.status_code}: {resp.text}"
            )

        payload = resp.json()
        access_token: str = payload["access_token"]
        expires_in: int = payload.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        token_ref.set({"access_token": access_token, "expires_at": expires_at})
        return access_token

    def resolve_track(self, soundcloud_url: str) -> Dict:
        token = self.get_token()

        try:
            resp = requests.get(
                "https://api.soundcloud.com/resolve",
                params={"url": soundcloud_url},
                headers={"Authorization": f"OAuth {token}"},
                allow_redirects=True,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SoundCloudAPIError(f"SoundCloud resolve request failed: {exc}") from exc

        if resp.status_code == 404:
            raise SoundCloudTrackNotFoundError("SoundCloud track not found")

        if not resp.ok:
            raise SoundCloudAPIError(
                f"SoundCloud API returned {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        access = data.get("access", "")
        if access != "playable":
            raise SoundCloudTrackNotPlayableError(
                f"SoundCloud track is not playable (access='{access}')"
            )

        genre = data.get("genre")
        return {
            "soundcloud_track_id": str(data["id"]),
            "title": data["title"],
            "soundcloud_url": data["permalink_url"],
            "soundcloud_artwork_url": data.get("artwork_url"),
            "soundcloud_stream_url": data.get("stream_url"),
            "soundcloud_waveform_url": data.get("waveform_url"),
            "duration": data["duration"],
            "access": access,
            "genres": [genre] if genre else [],
        }


class FixtureSoundCloudService:
    def resolve_track(self, soundcloud_url: str) -> Dict:
        if soundcloud_url != "https://soundcloud.com/mcp-fixtures/demo-track":
            raise SoundCloudTrackNotFoundError("No local fixture for this SoundCloud URL")
        return {
            "soundcloud_track_id": "FAKE-TRACK-1", "title": "Local demo track",
            "soundcloud_url": soundcloud_url, "soundcloud_artwork_url": None,
            "soundcloud_stream_url": None, "soundcloud_waveform_url": None,
            "duration": 60000, "access": "playable", "genres": ["Fixture"],
        }


class DisabledSoundCloudService:
    def resolve_track(self, soundcloud_url: str) -> Dict:
        raise SoundCloudAPIError("SoundCloud integration disabled")


def build_soundcloud_service(settings=None):
    settings = settings or get_runtime_settings()
    provider = settings.providers
    if provider.soundcloud == ProviderMode.FAKE:
        return FixtureSoundCloudService()
    if provider.soundcloud == ProviderMode.DISABLED:
        return DisabledSoundCloudService()
    if provider.soundcloud not in {ProviderMode.STAGING, ProviderMode.LIVE}:
        raise RuntimeConfigurationError("Unsupported SoundCloud mode")
    if not provider.soundcloud_client_id or not provider.soundcloud_client_secret:
        raise RuntimeConfigurationError("SoundCloud requires client ID and client secret")
    return SoundCloudService(provider.soundcloud_client_id.get_secret_value(),
                             provider.soundcloud_client_secret.get_secret_value())
