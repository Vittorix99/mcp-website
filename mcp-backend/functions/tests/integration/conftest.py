import os
import base64
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from api.admin import members_api, messages_api, purchases_api
from services.communications.mail_service import get_mail_config
from config.firebase_config import bucket as storage_bucket

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_FUNCTIONS_DIR = Path(__file__).resolve().parents[2]
_INTEGRATION_ENV = _FUNCTIONS_DIR / ".env.integration"

if _INTEGRATION_ENV.exists():
    # Keep explicit shell-provided values as precedence.
    load_dotenv(_INTEGRATION_ENV, override=False)

_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6Xb9oAAAAAASUVORK5CYII="
)


@pytest.fixture(autouse=True)
def _mock_admin_auth(monkeypatch):
    """Bypass Firebase admin token verification for integration API tests."""
    from services.core import auth_service

    monkeypatch.setattr(
        auth_service,
        "verify_admin_token",
        lambda _token: {"uid": "admin-test", "admin": True},
    )


@pytest.fixture(autouse=True)
def _patch_flask_request_proxies(monkeypatch):
    """Avoid LocalProxy teardown issues when tests monkeypatch request.get_json."""
    monkeypatch.setattr(members_api, "request", type("ReqStub", (), {"get_json": lambda *args, **kwargs: None})())
    monkeypatch.setattr(messages_api, "request", type("ReqStub", (), {"get_json": lambda *args, **kwargs: None})())
    monkeypatch.setattr(purchases_api, "request", type("ReqStub", (), {"get_json": lambda *args, **kwargs: None})())


@pytest.fixture(scope="session")
def gmail_service():
    pytest.skip("Gmail integration tests disabled after migration to MailerSend")


@pytest.fixture(scope="session")
def mailersend_api_key():
    try:
        config = get_mail_config()
    except Exception as exc:
        pytest.skip(f"MailerSend integration not configured: {exc}")
    if not config.api_key or not config.from_email:
        pytest.skip("MailerSend integration not configured: missing API key or sender email")
    return config.api_key


@pytest.fixture(scope="session", autouse=True)
def _ensure_storage_assets():
    if os.environ.get("SKIP_STORAGE_ASSET_BOOTSTRAP", "").lower() in {"1", "true", "yes"}:
        return
    if storage_bucket is None:
        return

    def _read_asset_bytes(path: str):
        candidates = [
            _ASSETS_DIR / path,
            _ASSETS_DIR / Path(path).name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.read_bytes()
        return None

    def _ensure_blob(path: str, payload: bytes, content_type: str = "image/png", make_public: bool = False):
        blob = storage_bucket.blob(path)
        if not blob.exists():
            blob.upload_from_string(payload, content_type=content_type)
        if make_public:
            blob.make_public()
        return blob

    logo_bytes = _read_asset_bytes("logos/logo_white.png") or _PLACEHOLDER_PNG
    logo_blob = _ensure_blob("logos/logo_white.png", logo_bytes, make_public=True)
    if not os.environ.get("LOGO_URL"):
        os.environ["LOGO_URL"] = logo_blob.public_url

    pattern_bytes = _read_asset_bytes("patterns/FINAL MCP PATTERN - ORANGE.png") or _PLACEHOLDER_PNG
    _ensure_blob("patterns/FINAL MCP PATTERN - ORANGE.png", pattern_bytes)


@pytest.fixture
def unique_email():
    base = os.environ.get("MAILERLITE_TEST_EMAIL_BASE", "mcpweb.test@gmail.com")
    local, domain = base.split("@", 1)
    return f"{local}+mail_{uuid4().hex[:8]}@{domain}"


@pytest.fixture
def unique_subject():
    return f"Integration mail test {uuid4().hex[:8]}"
