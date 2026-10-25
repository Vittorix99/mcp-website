import types

from api.admin import messages_api
from dto.message_api import MessageActionResponseDTO
from errors.service_errors import ExternalServiceError, NotFoundError
from tests.utils import DummyRequest, unwrap_response


def test_get_messages_invalid_method():
    resp, status = unwrap_response(messages_api.get_messages(DummyRequest(method="POST")))
    assert status == 405


def test_get_messages_happy_path(monkeypatch):
    item = types.SimpleNamespace(to_payload=lambda: {"id": "msg-1"})
    monkeypatch.setattr(messages_api, "messages_service", types.SimpleNamespace(get_all=lambda: [item]))
    resp, status = unwrap_response(messages_api.get_messages(DummyRequest(method="GET")))
    assert status == 200
    assert resp == [{"id": "msg-1"}]


def test_delete_message_missing_id_does_not_call_service(monkeypatch):
    called = False

    def delete(_message_id):
        nonlocal called
        called = True

    monkeypatch.setattr(messages_api, "messages_service", types.SimpleNamespace(delete_by_id=delete))
    resp, status = unwrap_response(messages_api.delete_message(DummyRequest(method="DELETE", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_delete_message_not_found(monkeypatch):
    def delete(_message_id):
        raise NotFoundError("missing")

    monkeypatch.setattr(messages_api, "messages_service", types.SimpleNamespace(delete_by_id=delete))
    resp, status = unwrap_response(
        messages_api.delete_message(DummyRequest(method="DELETE", json={"message_id": "msg-1"}))
    )
    assert status == 404
    assert resp["error"] == "missing"


def test_reply_to_message_missing_fields_does_not_call_service(monkeypatch):
    called = False

    def reply(_dto):
        nonlocal called
        called = True

    monkeypatch.setattr(messages_api, "messages_service", types.SimpleNamespace(reply=reply))
    resp, status = unwrap_response(messages_api.reply_to_message(DummyRequest(method="POST", json={"email": "a@b.com"})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_reply_to_message_external_error(monkeypatch):
    captured = {}

    def reply(dto):
        captured["dto"] = dto
        raise ExternalServiceError("boom")

    monkeypatch.setattr(messages_api, "messages_service", types.SimpleNamespace(reply=reply))
    req = DummyRequest(
        method="POST", json={"email": "a@b.com", "body": "hi", "message_id": "msg-1"}
    )
    resp, status = unwrap_response(messages_api.reply_to_message(req))
    assert status == 502
    assert resp["error"] == "boom"
    assert captured["dto"].message_id == "msg-1"


def test_reply_to_message_happy_path(monkeypatch):
    captured = {}

    def reply(dto):
        captured["dto"] = dto
        return MessageActionResponseDTO(message="sent", email_sent_to=dto.email)

    monkeypatch.setattr(messages_api, "messages_service", types.SimpleNamespace(reply=reply))
    req = DummyRequest(
        method="POST", json={"email": "a@b.com", "body": "hi", "message_id": "msg-1"}
    )
    resp, status = unwrap_response(messages_api.reply_to_message(req))
    assert status == 200
    assert resp["message"] == "sent"
    assert resp["emailSentTo"] == "a@b.com"
    assert captured["dto"].body == "hi"
