from types import SimpleNamespace

import pytest

from api.admin import members_api, messages_api, purchases_api
import services.sender.sender_service as sender_service_module
from services.sender.sender_service import SenderService


@pytest.fixture(autouse=True)
def _patch_flask_request_proxies(monkeypatch):
    """Replace Flask LocalProxy request objects with plain stubs for unit tests."""
    monkeypatch.setattr(members_api, "request", SimpleNamespace(get_json=lambda *args, **kwargs: None))
    monkeypatch.setattr(messages_api, "request", SimpleNamespace(get_json=lambda *args, **kwargs: None))
    monkeypatch.setattr(purchases_api, "request", SimpleNamespace(get_json=lambda *args, **kwargs: None))


@pytest.fixture
def sender_service():
    return SenderService(api_key="test-key-123")


@pytest.fixture
def mock_routes(monkeypatch):
    mocked = SimpleNamespace()
    monkeypatch.setattr(sender_service_module, "SenderRoutes", mocked)
    return mocked


@pytest.fixture
def sample_sender_error_payload():
    return {
        "error": [
            {"title": "Unsubscribe link", "details": "Insert this code..."},
            {"title": "DMARC record is not set up", "details": "The domain..."},
        ],
        "sent": False,
    }
