import types

from api.admin.mailer_lite import fields_api
from tests.utils import DummyRequest, unwrap_response


def test_fields_create_calls_client(monkeypatch):
    called = {}

    def fake_create(name, field_type):
        called["name"] = name
        called["type"] = field_type
        return {"data": {"id": 1}}

    monkeypatch.setattr(
        fields_api,
        "fields_client",
        types.SimpleNamespace(create=fake_create),
    )

    req = DummyRequest(method="POST", json={"name": "gender", "type": "text"})
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 200
    assert resp["data"]["id"] == 1
    assert called["name"] == "gender"


def test_fields_create_missing_name():
    req = DummyRequest(method="POST", json={"type": "text"})
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 400
    assert "Missing field name or type" in resp["error"]


def test_fields_list(monkeypatch):
    monkeypatch.setattr(
        fields_api,
        "fields_client",
        types.SimpleNamespace(list=lambda params=None: {"data": []}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 200
    assert resp == {"data": []}


def test_fields_update_missing_id():
    req = DummyRequest(method="PUT", json={"name": "x"})
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 400
    assert "Missing field id" in resp["error"]


def test_fields_update_missing_name():
    req = DummyRequest(method="PUT", json={"id": 1})
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 400
    assert "Missing field name" in resp["error"]


def test_fields_delete_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 400
    assert "Missing field id" in resp["error"]


def test_fields_invalid_method():
    req = DummyRequest(method="PATCH")
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 405


def test_fields_mailerlite_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise fields_api.MailerLiteError("boom", status=500, payload={"detail": "x"})

    monkeypatch.setattr(
        fields_api,
        "fields_client",
        types.SimpleNamespace(list=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(fields_api.admin_mailerlite_fields(req))
    assert status == 500
    assert resp["error"] == "MailerLite request failed"
