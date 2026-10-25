import json

import pytest

from config.runtime_settings import (
    CredentialMode,
    ProviderMode,
    RuntimeConfigurationError,
    clear_runtime_settings_cache,
    get_runtime_settings,
    load_runtime_settings,
    safe_runtime_summary,
)


@pytest.mark.parametrize("environment,project,credential", [
    ("local", "demo-mcp-local", CredentialMode.EMULATOR),
    ("test", "demo-mcp-test", CredentialMode.EMULATOR),
    ("staging", "mcp-website-dev-39539", CredentialMode.ADC),
    ("production", "mcp-website-2a1ad", CredentialMode.ADC),
])
def test_valid_environment_selects_its_resources(environment, project, credential):
    settings = load_runtime_settings({"MCP_ENV": environment})
    assert settings.firebase.project_id == project
    assert settings.firebase.credential_mode == credential


@pytest.mark.parametrize("environment", ["", "prod", "development", "oops"])
def test_unknown_environment_is_rejected(environment):
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": environment})


def test_environment_must_be_explicit():
    with pytest.raises(RuntimeConfigurationError, match="MCP_ENV"):
        load_runtime_settings({})


@pytest.mark.parametrize("key,value", [
    ("GCLOUD_PROJECT", "mcp-website-2a1ad"),
    ("GOOGLE_CLOUD_PROJECT", "mcp-website-dev-39539"),
    ("STORAGE_BUCKET", "mcp-website-2a1ad.appspot.com"),
    ("BACKEND_URL", "https://production.example.com"),
    ("GOOGLE_APPLICATION_CREDENTIALS", "/secret/sentinel.json"),
    ("FIREBASE_SERVICE_ACCOUNT_JSON", "SENTINEL_RAW_JSON"),
    ("PAYPAL_LIVE_CLIENT_SECRET", "SENTINEL_LIVE_SECRET"),
])
def test_local_rejects_production_project_and_bucket(key, value):
    with pytest.raises(RuntimeConfigurationError) as error:
        load_runtime_settings({"MCP_ENV": "local", key: value})
    assert value not in str(error.value)


@pytest.mark.parametrize("provider", ["PAYPAL", "MAIL", "SENDER", "PASS2U", "GENDER", "SOUNDCLOUD"])
def test_test_rejects_live_provider_mode_even_when_key_exists(provider):
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "test", f"{provider}_MODE": "live", f"{provider}_API_KEY": "sentinel"})


def test_staging_rejects_production_project():
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "staging", "GCLOUD_PROJECT": "mcp-website-2a1ad"})


@pytest.mark.parametrize("patch", [
    {"FIRESTORE_EMULATOR_HOST": "127.0.0.1:8080"},
    {"FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099"},
    {"BACKEND_URL": "http://localhost:5001"},
    {"PAYPAL_MODE": "sandbox"},
    {"GCLOUD_PROJECT": "demo-mcp-test"},
    {"STORAGE_BUCKET": "demo-mcp-test.appspot.com"},
    {"PAYPAL_ENV": "sandbox"},
])
def test_production_rejects_emulator_host_localhost_and_paypal_sandbox(patch):
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "production", **patch})


def test_provider_key_does_not_enable_provider():
    settings = load_runtime_settings({"MCP_ENV": "test", "SENDER_API_KEY": "sentinel"})
    assert settings.providers.sender == ProviderMode.DISABLED


@pytest.mark.parametrize("key", ["FIRESTORE_EMULATOR_HOST", "FIREBASE_AUTH_EMULATOR_HOST", "STORAGE_EMULATOR_HOST", "PUBSUB_EMULATOR_HOST"])
def test_explicit_missing_emulator_host_is_rejected(key):
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "test", key: ""})


@pytest.mark.parametrize("host", ["firestore.googleapis.com:443", "localhost.evil.example:8080", "https://127.0.0.1:8080", "127.0.0.1", "127.0.0.1:99999"])
def test_emulators_accept_only_loopback_host_and_valid_port(host):
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "test", "FIRESTORE_EMULATOR_HOST": host})


def test_conflicting_project_aliases_are_rejected():
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "test", "GCLOUD_PROJECT": "demo-mcp-test", "GOOGLE_CLOUD_PROJECT": "mcp-website-2a1ad"})


def test_firebase_config_cannot_override_project():
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "test", "FIREBASE_CONFIG": json.dumps({"projectId": "mcp-website-2a1ad"})})


def test_staging_mail_requires_recipient_allowlist():
    with pytest.raises(RuntimeConfigurationError):
        load_runtime_settings({"MCP_ENV": "staging", "MAIL_MODE": "staging"})


def test_safe_summary_contains_modes_but_no_secret_values():
    settings = load_runtime_settings({"MCP_ENV": "test", "SENDER_API_KEY": "SECRET_SENTINEL", "MAILERSEND_API_KEY": "SECRET_SENTINEL"})
    summary = safe_runtime_summary(settings)
    assert summary["environment"] == "test"
    assert summary["providers"]["paypal"] == "fake"
    assert summary["credential_presence"]["sender"] is True
    assert "SECRET_SENTINEL" not in json.dumps(summary)
    assert "SECRET_SENTINEL" not in repr(settings)


def test_cached_settings_are_immutable_and_resettable(monkeypatch):
    monkeypatch.setenv("MCP_ENV", "test")
    # Inject an empty mapping into the loader separately; host process may
    # contain legacy vars, so this test explicitly clears relevant keys.
    for key in ("GCLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS", "FIREBASE_CONFIG", "STORAGE_BUCKET"):
        monkeypatch.delenv(key, raising=False)
    clear_runtime_settings_cache()
    first = get_runtime_settings()
    assert first is get_runtime_settings()
    with pytest.raises(Exception):
        first.firebase.project_id = "other"
    clear_runtime_settings_cache()
    assert first is not get_runtime_settings()
    clear_runtime_settings_cache()
