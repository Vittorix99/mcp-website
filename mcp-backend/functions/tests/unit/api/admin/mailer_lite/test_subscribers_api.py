import types

from api.admin.mailer_lite import subscribers_api
from tests.utils import DummyRequest, unwrap_response


def test_subscribers_create_calls_client(monkeypatch):
    called = {}

    def fake_create(email, payload):
        called["email"] = email
        called["payload"] = payload
        return {"data": {"id": 123, "email": email}}

    monkeypatch.setattr(
        subscribers_api,
        "subscribers_client",
        types.SimpleNamespace(create=fake_create),
    )

    req = DummyRequest(method="POST", json={"email": "a@b.com", "fields": {"name": "A"}})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))

    assert status == 200
    assert resp["data"]["id"] == 123
    assert called["email"] == "a@b.com"


def test_subscribers_create_missing_email():
    req = DummyRequest(method="POST", json={"fields": {"name": "A"}})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 400
    assert resp["error"] == "Missing email"


def test_subscribers_get_by_email(monkeypatch):
    monkeypatch.setattr(
        subscribers_api,
        "subscribers_client",
        types.SimpleNamespace(get=lambda email: {"email": email}),
    )
    req = DummyRequest(method="GET", args={"email": "x@y.com"})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 200
    assert resp["email"] == "x@y.com"


def test_subscribers_list(monkeypatch):
    monkeypatch.setattr(
        subscribers_api,
        "subscribers_client",
        types.SimpleNamespace(list=lambda params=None: {"data": []}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 200
    assert resp == {"data": []}


def test_subscribers_update_missing_email():
    req = DummyRequest(method="PUT", json={"fields": {"name": "A"}})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 400
    assert "Missing email" in resp["error"]


def test_subscribers_delete_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 400
    assert "Missing subscriber id" in resp["error"]


def test_subscriber_forget_missing_id():
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscriber_forget(req))
    assert status == 400
    assert "Missing subscriber id" in resp["error"]


def test_subscriber_forget_calls_client(monkeypatch):
    monkeypatch.setattr(
        subscribers_api,
        "subscribers_client",
        types.SimpleNamespace(forget_subscriber=lambda subscriber_id: {"ok": True}),
    )
    req = DummyRequest(method="POST", json={"subscriber_id": 1})
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscriber_forget(req))
    assert status == 200
    assert resp["ok"] is True


def test_subscribers_invalid_method():
    req = DummyRequest(method="PATCH")
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 405


def test_subscriber_forget_invalid_method():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscriber_forget(req))
    assert status == 405


def test_subscribers_mailerlite_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise subscribers_api.MailerLiteError("boom", status=502, payload={"detail": "x"})

    monkeypatch.setattr(
        subscribers_api,
        "subscribers_client",
        types.SimpleNamespace(list=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(req))
    assert status == 502
    assert resp["error"] == "MailerLite request failed"
