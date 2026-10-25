import hashlib

import pytest

from config.runtime_settings import RuntimeConfigurationError, load_runtime_settings
from tests.config_fixtures import cloud_environment
from services.memberships.pass2u_service import (
    DisabledPass2UService,
    FakePass2UService,
    build_pass2u_service,
)


def test_local_fake_pass_is_deterministic_and_offline(monkeypatch):
    def fail_if_called(**kwargs):
        pytest.fail("fake Pass2U service called Pass2URoutes")

    monkeypatch.setattr("services.memberships.pass2u_service.Pass2URoutes.create_pass", fail_if_called)
    monkeypatch.setattr("services.memberships.pass2u_service.Pass2URoutes.invalidate_pass", fail_if_called)
    membership = object()
    first = build_pass2u_service(load_runtime_settings({"MCP_ENV": "local"}))
    second = build_pass2u_service(load_runtime_settings({"MCP_ENV": "local"}))

    result = first.create_membership_pass("member-1", membership)
    expected_id = "FAKE-" + hashlib.sha256(b"member-1").hexdigest()[:16]
    assert isinstance(first, FakePass2UService)
    assert result.pass_id == expected_id
    assert second.create_membership_pass("member-1", membership).pass_id == result.pass_id
    assert result.wallet_url == "http://127.0.0.1:3000/local-wallet/member-1"
    assert result.apple_wallet_url == result.wallet_url
    assert result.google_wallet_url == result.wallet_url
    assert first.invalidate_membership_pass(expected_id) is True
    assert first.invalidate_membership_pass("external-pass-id") is False


def test_staging_default_pass2u_service_is_disabled():
    service = build_pass2u_service(load_runtime_settings(cloud_environment("staging")))
    assert isinstance(service, DisabledPass2UService)
    assert service.create_membership_pass("member-1", object()) is None
    assert service.invalidate_membership_pass("FAKE-123") is False


def test_production_live_without_key_raises_redacted_configuration_error():
    settings = load_runtime_settings(cloud_environment("production"))
    settings = settings.model_copy(update={"providers": settings.providers.model_copy(update={"pass2u_api_key": None})})
    with pytest.raises(RuntimeConfigurationError) as exc:
        build_pass2u_service(settings)
    assert "PASS2U_API_KEY" in str(exc.value)
    assert "sentinel" not in str(exc.value)
