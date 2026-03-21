import types

from api.public import contact_api
from errors.service_errors import ExternalServiceError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_contact_us_invalid_method():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 405
    assert resp == "Invalid request method"


def test_contact_us_missing_body():
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 400
    assert resp == "Invalid request"


def test_contact_us_happy_path(monkeypatch):
    captured = {}

    def fake_submit(dto, send_copy=False):
        captured["name"] = dto.name
        captured["email"] = dto.email
        captured["send_copy"] = send_copy
        return {"message": "ok"}

    monkeypatch.setattr(
        contact_api,
        "messages_service",
        types.SimpleNamespace(submit_contact_message=fake_submit),
    )

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
    assert resp["message"] == "ok"
    assert captured["name"] == "Mario Rossi"
    assert captured["email"] == "mario@example.com"
    assert captured["send_copy"] is True


def test_contact_us_validation_error(monkeypatch):
    monkeypatch.setattr(
        contact_api,
        "messages_service",
        types.SimpleNamespace(
            submit_contact_message=lambda *_args, **_kwargs: (_ for _ in ()).throw(ValidationError("bad payload"))
        ),
    )

    req = DummyRequest(method="POST", json={"name": "Mario", "email": "mario@example.com", "message": "x"})
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 400
    assert resp["error"] == "bad payload"


def test_contact_us_external_service_error(monkeypatch):
    monkeypatch.setattr(
        contact_api,
        "messages_service",
        types.SimpleNamespace(
            submit_contact_message=lambda *_args, **_kwargs: (_ for _ in ()).throw(ExternalServiceError("mail down"))
        ),
    )

    req = DummyRequest(method="POST", json={"name": "Mario", "email": "mario@example.com", "message": "x"})
    resp, status = unwrap_response(contact_api.contact_us(req))
    assert status == 502
    assert resp["error"] == "mail down"
