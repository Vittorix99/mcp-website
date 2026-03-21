from unittest.mock import MagicMock

import pytest

from api.admin.sender import helpers as sender_helpers
from services.sender.sender_service import SenderService


@pytest.fixture(autouse=True)
def _force_sender_service(monkeypatch):
    """Use a deterministic Sender service instance for API integration tests."""
    monkeypatch.setattr(sender_helpers, "_sender_service", SenderService(api_key="test-key"))


@pytest.fixture
def sender_response_factory():
    """Build a minimal requests.Response-like mock."""

    def _factory(status_code: int, payload):
        response = MagicMock()
        response.status_code = status_code
        if payload is None:
            response.content = b""
            response.json.side_effect = ValueError("no json")
        else:
            response.content = b"x"
            response.json.return_value = payload
        return response

    return _factory
