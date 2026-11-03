import types

from api.public import contact_api
from dto.message_api import ContactMessageResponseDTO
from errors.service_errors import ExternalServiceError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_contact_us_invalid_method():
    resp, status = unwrap_response(contact_api.contact_us(DummyRequest(method="GET")))
    assert status == 405
    assert resp["error"] == "Invalid method"


def test_contact_us_missing_body_does_not_call_service(monkeypatch):
    called = False

    def submit(_dto):
        nonlocal called
        called = True

    monkeypatch.setattr(contact_api, "messages_service", types.SimpleNamespace(submit_contact_message=submit))
    resp, status = unwrap_response(contact_api.contact_us(DummyRequest(method="POST", json=None)))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_contact_us_happy_path(monkeypatch):
    captured = {}

    def submit(dto):
        captured["dto"] = dto
        return ContactMessageResponseDTO(id="message-1", name=dto.name, email=dto.email, message=dto.message)

    monkeypatch.setattr(contact_api, "messages_service", types.SimpleNamespace(submit_contact_message=submit))
    req = DummyRequest(
        method="POST",
        json={
            "name": "Mario Rossi",
            "email": "mario@example.com",
            "message": "Ciao",
            "send_copy": True,
        },
    )
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 200
    assert resp["id"] == "message-1"
    assert captured["dto"].name == "Mario Rossi"
    assert str(captured["dto"].email) == "mario@example.com"
    assert captured["dto"].message == "Ciao"
    assert captured["dto"].send_copy is True


def test_contact_us_service_validation_error(monkeypatch):
    def submit(_dto):
        raise ValidationError("bad payload")

    monkeypatch.setattr(contact_api, "messages_service", types.SimpleNamespace(submit_contact_message=submit))
    req = DummyRequest(method="POST", json={"name": "Mario", "email": "mario@example.com", "message": "x"})
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 400
    assert resp["error"] == "bad payload"


def test_contact_us_external_service_error(monkeypatch):
    def submit(_dto):
        raise ExternalServiceError("mail down")

    monkeypatch.setattr(contact_api, "messages_service", types.SimpleNamespace(submit_contact_message=submit))
    req = DummyRequest(method="POST", json={"name": "Mario", "email": "mario@example.com", "message": "x"})
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 502
    assert resp["error"] == "mail down"
