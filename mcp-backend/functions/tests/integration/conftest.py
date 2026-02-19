import os
import base64
from pathlib import Path
from uuid import uuid4

import pytest

from services.mail_service import get_mail_config, _build_gmail_service
from tests.integration.gmail_utils import ensure_read_scopes
from config.firebase_config import bucket as storage_bucket

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6Xb9oAAAAAASUVORK5CYII="
)


@pytest.fixture(autouse=True)
def _mock_admin_auth(monkeypatch):
    """Bypass Firebase admin token verification for integration API tests."""
    from services import auth_service

    monkeypatch.setattr(
        auth_service,
        "verify_admin_token",
        lambda _token: {"uid": "admin-test", "admin": True},
    )


@pytest.fixture(scope="session")
def gmail_service():
    config = get_mail_config()
    if not config.user_email:
        pytest.skip("USER_EMAIL is not set for Gmail integration tests")
    try:
        ensure_read_scopes(config.scopes)
    except RuntimeError as exc:
        pytest.fail(str(exc))
    return _build_gmail_service(config)


@pytest.fixture(scope="session", autouse=True)
def _ensure_storage_assets():
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
