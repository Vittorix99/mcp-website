import types

from api.admin.mailer_lite import automations_api
from tests.utils import DummyRequest, unwrap_response


def test_automations_list(monkeypatch):
    monkeypatch.setattr(
        automations_api,
        "automations_client",
        types.SimpleNamespace(list=lambda params=None: {"data": []}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(automations_api.admin_mailerlite_automations(req))
    assert status == 200
    assert resp == {"data": []}


def test_automations_get(monkeypatch):
    monkeypatch.setattr(
        automations_api,
        "automations_client",
        types.SimpleNamespace(get=lambda automation_id: {"id": automation_id}),
    )
    req = DummyRequest(method="GET", args={"id": "9"})
    resp, status = unwrap_response(automations_api.admin_mailerlite_automations(req))
    assert status == 200
    assert resp["id"] == "9"


def test_automation_activity_missing_id():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(automations_api.admin_mailerlite_automation_activity(req))
    assert status == 400
    assert "Missing automation_id" in resp["error"]


def test_automations_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(automations_api.admin_mailerlite_automations(req))
    assert status == 405


def test_automation_activity_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(automations_api.admin_mailerlite_automation_activity(req))
    assert status == 405


def test_automations_mailerlite_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise automations_api.MailerLiteError("boom", status=500, payload={"detail": "x"})

    monkeypatch.setattr(
        automations_api,
        "automations_client",
        types.SimpleNamespace(list=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(automations_api.admin_mailerlite_automations(req))
    assert status == 500
    assert resp["error"] == "MailerLite request failed"
