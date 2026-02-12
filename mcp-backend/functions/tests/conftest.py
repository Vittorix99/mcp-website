import os
import sys
from pathlib import Path

import pytest
from flask import Flask
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services import auth_service

_env_path = Path(__file__).resolve().parents[1] / ".env"
_integration_env_path = Path(__file__).resolve().parents[1] / ".env.integration"
load_dotenv(dotenv_path=_env_path, override=False)
if _integration_env_path.exists():
    load_dotenv(dotenv_path=_integration_env_path, override=True)


@pytest.fixture(autouse=True)
def _bypass_admin_auth(monkeypatch):
    monkeypatch.setattr(
        auth_service.auth,
        "verify_id_token",
        lambda token: {"admin": True},
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
