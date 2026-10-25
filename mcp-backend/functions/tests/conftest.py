import os
import sys

import pytest
from flask import Flask

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["MCP_ENV"] = "test"
os.environ["GCLOUD_PROJECT"] = "demo-mcp-test"
os.environ["GOOGLE_CLOUD_PROJECT"] = "demo-mcp-test"
os.environ["STORAGE_BUCKET"] = "demo-mcp-test.appspot.com"
for key, value in {
    "FIRESTORE_EMULATOR_HOST": "127.0.0.1:8080",
    "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099",
    "STORAGE_EMULATOR_HOST": "127.0.0.1:9199",
    "PUBSUB_EMULATOR_HOST": "127.0.0.1:8085",
}.items():
    os.environ.setdefault(key, value)

from services.core import auth_service


@pytest.fixture(autouse=True)
def _bypass_admin_auth(monkeypatch):
    monkeypatch.setattr(
        auth_service.auth,
        "verify_id_token",
        lambda token: {"admin": True, "uid": "test-admin"},
    )
    yield


@pytest.fixture(autouse=True)
def _app_context():
    app = Flask("tests")
    with app.app_context():
        yield


@pytest.fixture(autouse=True)
def _request_context():
    app = Flask("tests-request")
    with app.test_request_context("/"):
        yield
