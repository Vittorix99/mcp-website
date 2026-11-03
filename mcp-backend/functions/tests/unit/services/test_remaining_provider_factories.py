import pytest

from config.runtime_settings import load_runtime_settings
from tests.config_fixtures import cloud_environment
from errors.service_errors import SoundCloudTrackNotFoundError


def test_gender_fixture_is_deterministic_and_never_uses_http():
    from services.gender.gender_service import build_gender_lookup
    provider = build_gender_lookup(load_runtime_settings({"MCP_ENV": "test"}))
    assert provider.lookup("Giulia Bianchi") == ("female", 1.0)
    assert provider.lookup("Andrea") == ("male", 1.0)
    assert provider.lookup("unknown") == ("N/A", 0.0)


def test_disabled_gender_does_not_infer_personal_attributes():
    from services.gender.gender_service import build_gender_lookup
    provider = build_gender_lookup(load_runtime_settings({**cloud_environment("production"), "GENDER_MODE": "disabled"}))
    assert provider.lookup("Giulia") == ("N/A", 0.0)


def test_soundcloud_fixture_uses_explicit_local_track_only():
    from services.soundcloud.soundcloud_service import build_soundcloud_service
    provider = build_soundcloud_service(load_runtime_settings({"MCP_ENV": "test"}))
    result = provider.resolve_track("https://soundcloud.com/mcp-fixtures/demo-track")
    assert result["soundcloud_track_id"] == "FAKE-TRACK-1"
    assert result["duration"] == 60000
    with pytest.raises(SoundCloudTrackNotFoundError):
        provider.resolve_track("https://soundcloud.com/other/unknown")
