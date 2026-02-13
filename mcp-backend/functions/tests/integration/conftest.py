import os
from uuid import uuid4

import pytest

from services.mail_service import get_mail_config, _build_gmail_service
from tests.integration.gmail_utils import ensure_read_scopes


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


@pytest.fixture
def unique_email():
    base = os.environ.get("MAILERLITE_TEST_EMAIL_BASE", "mcpweb.testing@gmail.com")
    local, domain = base.split("@", 1)
    return f"{local}+mail_{uuid4().hex[:8]}@{domain}"


@pytest.fixture
def unique_subject():
    return f"Integration mail test {uuid4().hex[:8]}"
