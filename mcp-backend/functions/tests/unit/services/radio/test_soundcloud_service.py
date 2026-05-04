"""Unit tests for SoundCloudService — no real HTTP calls, no Firestore."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from errors.service_errors import (
    SoundCloudAPIError,
    SoundCloudAuthError,
    SoundCloudTrackNotFoundError,
    SoundCloudTrackNotPlayableError,
)
from services.soundcloud.soundcloud_service import SoundCloudService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(access_token="tok", expires_delta_seconds=3600):
    """Return a Firestore-like document snapshot stub."""
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "access_token": access_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_delta_seconds),
    }
    return doc


def _missing_doc():
    doc = MagicMock()
    doc.exists = False
    return doc


def _make_service():
    return SoundCloudService()


# ---------------------------------------------------------------------------
# get_token — cache hit
# ---------------------------------------------------------------------------

def test_get_token_returns_cached_token_when_valid():
    svc = _make_service()
    doc = _make_doc(access_token="cached-token", expires_delta_seconds=3600)

    with patch("services.soundcloud.soundcloud_service.db") as mock_db:
        mock_db.collection.return_value.document.return_value.get.return_value = doc
        token = svc.get_token()

    assert token == "cached-token"


def test_get_token_refreshes_when_token_near_expiry():
    svc = _make_service()
    # expires in 2 minutes — within the 5-minute grace window
    doc = _make_doc(access_token="old-token", expires_delta_seconds=120)

    new_token_response = MagicMock()
    new_token_response.ok = True
    new_token_response.json.return_value = {"access_token": "new-token", "expires_in": 3600}

    with patch("services.soundcloud.soundcloud_service.db") as mock_db, \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_ID", "id"), \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_SECRET", "secret"), \
         patch("requests.post", return_value=new_token_response):

        token_ref = MagicMock()
        token_ref.get.return_value = doc
        mock_db.collection.return_value.document.return_value = token_ref

        token = svc.get_token()

    assert token == "new-token"
    token_ref.set.assert_called_once()


def test_get_token_refreshes_when_no_doc():
    svc = _make_service()

    new_token_response = MagicMock()
    new_token_response.ok = True
    new_token_response.json.return_value = {"access_token": "fresh-token", "expires_in": 3600}

    with patch("services.soundcloud.soundcloud_service.db") as mock_db, \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_ID", "id"), \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_SECRET", "secret"), \
         patch("requests.post", return_value=new_token_response):

        token_ref = MagicMock()
        token_ref.get.return_value = _missing_doc()
        mock_db.collection.return_value.document.return_value = token_ref

        token = svc.get_token()

    assert token == "fresh-token"


def test_get_token_raises_auth_error_when_credentials_missing():
    svc = _make_service()

    with patch("services.soundcloud.soundcloud_service.db") as mock_db, \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_ID", None), \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_SECRET", None):

        mock_db.collection.return_value.document.return_value.get.return_value = _missing_doc()

        with pytest.raises(SoundCloudAuthError):
            svc.get_token()


def test_get_token_raises_auth_error_on_bad_http_response():
    svc = _make_service()

    bad_response = MagicMock()
    bad_response.ok = False
    bad_response.status_code = 401
    bad_response.text = "Unauthorized"

    with patch("services.soundcloud.soundcloud_service.db") as mock_db, \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_ID", "id"), \
         patch("services.soundcloud.soundcloud_service.SOUNDCLOUD_CLIENT_SECRET", "secret"), \
         patch("requests.post", return_value=bad_response):

        mock_db.collection.return_value.document.return_value.get.return_value = _missing_doc()

        with pytest.raises(SoundCloudAuthError):
            svc.get_token()


# ---------------------------------------------------------------------------
# resolve_track
# ---------------------------------------------------------------------------

SC_TRACK_RESPONSE = {
    "id": 12345,
    "title": "Test Track",
    "permalink_url": "https://soundcloud.com/artist/track",
    "artwork_url": "https://i1.sndcdn.com/artworks.jpg",
    "stream_url": "https://api.soundcloud.com/tracks/12345/stream",
    "waveform_url": "https://wave.sndcdn.com/track.png",
    "duration": 240000,
    "access": "playable",
    "genre": "House",
}


def _mock_get_token(svc, token="test-token"):
    svc.get_token = MagicMock(return_value=token)


def test_resolve_track_happy_path():
    svc = _make_service()
    _mock_get_token(svc)

    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = SC_TRACK_RESPONSE

    with patch("requests.get", return_value=response):
        result = svc.resolve_track("https://soundcloud.com/artist/track")

    assert result["soundcloud_track_id"] == "12345"
    assert result["title"] == "Test Track"
    assert result["duration"] == 240000
    assert result["access"] == "playable"
    assert result["genres"] == ["House"]


def test_resolve_track_no_genre_returns_empty_list():
    svc = _make_service()
    _mock_get_token(svc)

    track = dict(SC_TRACK_RESPONSE)
    track.pop("genre")

    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = track

    with patch("requests.get", return_value=response):
        result = svc.resolve_track("https://soundcloud.com/artist/track")

    assert result["genres"] == []


def test_resolve_track_raises_not_found_on_404():
    svc = _make_service()
    _mock_get_token(svc)

    response = MagicMock()
    response.ok = False
    response.status_code = 404

    with patch("requests.get", return_value=response):
        with pytest.raises(SoundCloudTrackNotFoundError):
            svc.resolve_track("https://soundcloud.com/missing")


def test_resolve_track_raises_not_playable_when_access_blocked():
    svc = _make_service()
    _mock_get_token(svc)

    track = dict(SC_TRACK_RESPONSE)
    track["access"] = "blocked"

    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = track

    with patch("requests.get", return_value=response):
        with pytest.raises(SoundCloudTrackNotPlayableError):
            svc.resolve_track("https://soundcloud.com/artist/track")


def test_resolve_track_raises_api_error_on_server_error():
    svc = _make_service()
    _mock_get_token(svc)

    response = MagicMock()
    response.ok = False
    response.status_code = 500
    response.text = "Internal Server Error"

    with patch("requests.get", return_value=response):
        with pytest.raises(SoundCloudAPIError):
            svc.resolve_track("https://soundcloud.com/artist/track")
