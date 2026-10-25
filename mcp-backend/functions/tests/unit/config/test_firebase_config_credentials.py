import importlib
from types import SimpleNamespace

import pytest
from google.auth.credentials import AnonymousCredentials

from config.runtime_settings import load_runtime_settings


@pytest.fixture
def firebase_module(monkeypatch):
    monkeypatch.setenv("MCP_ENV", "test")
    for key in ("GOOGLE_APPLICATION_CREDENTIALS", "FIREBASE_SERVICE_ACCOUNT_JSON", "GCLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT", "STORAGE_BUCKET", "FIREBASE_CONFIG"):
        monkeypatch.delenv(key, raising=False)
    from config.runtime_settings import clear_runtime_settings_cache
    clear_runtime_settings_cache()
    return importlib.import_module("config.firebase_config")


def _fake_constructors(module, monkeypatch):
    initialized = []
    monkeypatch.setattr(module.firebase_admin, "_apps", {})
    def initialize(credential, options):
        initialized.append((credential, options))
        return SimpleNamespace(project_id=options["projectId"])
    monkeypatch.setattr(module.firebase_admin, "initialize_app", initialize)
    monkeypatch.setattr(module.firestore, "client", lambda app: ("db", app.project_id))
    monkeypatch.setattr(module.storage, "bucket", lambda name, app: ("bucket", name))
    return initialized


def test_emulator_startup_does_not_read_service_account_json(firebase_module, monkeypatch):
    calls = _fake_constructors(firebase_module, monkeypatch)
    monkeypatch.setattr(firebase_module.credentials, "Certificate", lambda *args: pytest.fail("JSON credential read"))
    monkeypatch.setattr(firebase_module.credentials, "ApplicationDefault", lambda: pytest.fail("ADC attempted locally"))
    settings = load_runtime_settings({"MCP_ENV": "test"})
    db, bucket = firebase_module.initialize_firebase(settings)
    assert db == ("db", "demo-mcp-test")
    assert bucket == ("bucket", "demo-mcp-test.appspot.com")
    assert isinstance(calls[0][0].get_credential(), AnonymousCredentials)
    assert calls[0][1]["projectId"] == "demo-mcp-test"


def test_cloud_startup_uses_application_default_credentials(firebase_module, monkeypatch):
    calls = _fake_constructors(firebase_module, monkeypatch)
    credential = object()
    monkeypatch.setattr(firebase_module.credentials, "ApplicationDefault", lambda: credential)
    for key in ("FIRESTORE_EMULATOR_HOST", "FIREBASE_AUTH_EMULATOR_HOST", "STORAGE_EMULATOR_HOST", "PUBSUB_EMULATOR_HOST"):
        monkeypatch.delenv(key, raising=False)
    from tests.config_fixtures import cloud_environment
    db, bucket = firebase_module.initialize_firebase(load_runtime_settings(cloud_environment("staging")))
    assert db == ("db", "mcp-website-dev-39539")
    assert calls[0][0] is credential
