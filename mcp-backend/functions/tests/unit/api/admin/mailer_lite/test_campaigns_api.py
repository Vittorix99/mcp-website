import types

from api.admin.mailer_lite import campaigns_api
from tests.utils import DummyRequest, unwrap_response


def test_campaign_schedule_calls_client(monkeypatch):
    called = {}

    def fake_schedule(campaign_id, payload):
        called["id"] = campaign_id
        called["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(
        campaigns_api,
        "campaigns_client",
        types.SimpleNamespace(schedule=fake_schedule),
    )

    req = DummyRequest(method="POST", json={"campaign_id": 42, "delivery": "scheduled"})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaign_schedule(req))
    assert status == 200
    assert resp["ok"] is True
    assert called["id"] == 42


def test_campaign_schedule_missing_id():
    req = DummyRequest(method="POST", json={"delivery": "scheduled"})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaign_schedule(req))
    assert status == 400
    assert "Missing campaign id" in resp["error"]


def test_campaigns_get_by_id(monkeypatch):
    monkeypatch.setattr(
        campaigns_api,
        "campaigns_client",
        types.SimpleNamespace(get=lambda campaign_id: {"id": campaign_id}),
    )
    req = DummyRequest(method="GET", args={"id": "10"})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 200
    assert resp["id"] == "10"


def test_campaigns_list(monkeypatch):
    monkeypatch.setattr(
        campaigns_api,
        "campaigns_client",
        types.SimpleNamespace(list=lambda params=None: {"data": []}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 200
    assert resp == {"data": []}


def test_campaigns_create_missing_payload():
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 400
    assert "Missing payload" in resp["error"]


def test_campaigns_update_missing_id():
    req = DummyRequest(method="PUT", json={"name": "Test"})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 400
    assert "Missing campaign id" in resp["error"]


def test_campaigns_delete_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 400
    assert "Missing campaign id" in resp["error"]


def test_campaign_cancel_ready_calls_client(monkeypatch):
    called = {}

    def fake_cancel(campaign_id):
        called["id"] = campaign_id
        return {"ok": True}

    monkeypatch.setattr(
        campaigns_api,
        "campaigns_client",
        types.SimpleNamespace(cancel_ready=fake_cancel),
    )
    req = DummyRequest(method="POST", json={"campaign_id": 55})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaign_cancel_ready(req))
    assert status == 200
    assert resp["ok"] is True
    assert called["id"] == 55


def test_campaign_cancel_ready_missing_id():
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaign_cancel_ready(req))
    assert status == 400
    assert "Missing campaign id" in resp["error"]


def test_campaigns_invalid_method():
    req = DummyRequest(method="PATCH")
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 405


def test_campaign_schedule_invalid_method():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaign_schedule(req))
    assert status == 405


def test_campaign_cancel_invalid_method():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaign_cancel_ready(req))
    assert status == 405


def test_campaigns_mailerlite_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise campaigns_api.MailerLiteError("boom", status=503, payload={"detail": "x"})

    monkeypatch.setattr(
        campaigns_api,
        "campaigns_client",
        types.SimpleNamespace(list=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(campaigns_api.admin_mailerlite_campaigns(req))
    assert status == 503
    assert resp["error"] == "MailerLite request failed"
