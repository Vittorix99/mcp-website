import types

from api.admin import messages_api
from errors.service_errors import ExternalServiceError, NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_messages_invalid_method():
    """Rejects invalid method for listing messages."""
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(messages_api.get_messages(req))
    assert status == 405


def test_get_messages_happy_path(monkeypatch):
    """Returns messages list."""
    monkeypatch.setattr(
        messages_api,
        "messages_service",
        types.SimpleNamespace(get_all=lambda: [{"id": "msg-1"}]),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(messages_api.get_messages(req))
    assert status == 200
    assert resp == [{"id": "msg-1"}]


def test_delete_message_missing_id(monkeypatch):
    """Returns 400 when message_id is missing."""
    monkeypatch.setattr(messages_api.request, "get_json", lambda: {})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(messages_api.delete_message(req))
    assert status == 400
    assert resp["error"] == "Missing message_id"


def test_delete_message_not_found(monkeypatch):
    """Maps not found errors to 404."""
    monkeypatch.setattr(
        messages_api,
        "messages_service",
        types.SimpleNamespace(delete_by_id=lambda mid: (_ for _ in ()).throw(NotFoundError("missing"))),
    )
    monkeypatch.setattr(messages_api.request, "get_json", lambda: {"message_id": "msg-1"})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(messages_api.delete_message(req))
    assert status == 404
    assert resp["error"] == "missing"


def test_reply_to_message_missing_fields(monkeypatch):
    """Returns 400 when reply fields are missing."""
    monkeypatch.setattr(messages_api.request, "get_json", lambda: {"email": "a@b.com"})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(messages_api.reply_to_message(req))
    assert status == 400
    assert resp["error"] == "Missing email, message body or message ID"


def test_reply_to_message_external_error(monkeypatch):
    """Maps external errors to 502."""
    monkeypatch.setattr(
        messages_api,
        "messages_service",
        types.SimpleNamespace(reply=lambda *args, **kwargs: (_ for _ in ()).throw(ExternalServiceError("boom"))),
    )
    monkeypatch.setattr(
        messages_api.request,
        "get_json",
        lambda: {"email": "a@b.com", "body": "hi", "message_id": "msg-1"},
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(messages_api.reply_to_message(req))
    assert status == 502
    assert resp["error"] == "boom"
