from types import SimpleNamespace

import pytest

from api.admin import members_api, messages_api, purchases_api
import services.sender.sender_service as sender_service_module
from clients.sender_client import SenderRoutes
from services.sender.sender_service import SenderService


@pytest.fixture(autouse=True)
def _deny_unit_network(monkeypatch):
    """Unit tests inject external I/O; an absent fake must fail immediately."""
    import socket
    import urllib.request
    import requests
    from google.cloud.firestore_v1.client import Client

    def forbidden(*args, **kwargs):
        raise RuntimeError("Network is disabled in unit tests; inject the dependency")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    monkeypatch.setattr(Client, "_firestore_api", property(forbidden))


@pytest.fixture(autouse=True)
def _patch_flask_request_proxies(monkeypatch):
    """Replace Flask LocalProxy request objects with plain stubs for unit tests."""
    request_stub = SimpleNamespace(get_json=lambda *args, **kwargs: None)
    monkeypatch.setattr(members_api, "request", request_stub, raising=False)
    monkeypatch.setattr(messages_api, "request", request_stub, raising=False)
    monkeypatch.setattr(purchases_api, "request", request_stub, raising=False)


@pytest.fixture
def sender_service():
    return SenderService(api_key="fake-test-key-123", routes=SenderRoutes)


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
