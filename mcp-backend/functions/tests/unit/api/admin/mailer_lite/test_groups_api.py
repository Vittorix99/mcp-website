import types

from api.admin.mailer_lite import groups_api
from tests.utils import DummyRequest, unwrap_response


def test_groups_list_calls_client(monkeypatch):
    monkeypatch.setattr(
        groups_api,
        "groups_client",
        types.SimpleNamespace(list=lambda params=None: {"data": []}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(req))
    assert status == 200
    assert resp == {"data": []}


def test_groups_create_missing_name():
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(req))
    assert status == 400
    assert "Missing group name" in resp["error"]


def test_groups_update_missing_name():
    req = DummyRequest(method="PUT", json={"id": 1})
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(req))
    assert status == 400
    assert "Missing group name" in resp["error"]


def test_groups_delete_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(req))
    assert status == 400
    assert "Missing group id" in resp["error"]


def test_group_subscribers_missing_id():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_subscribers(req))
    assert status == 400
    assert "Missing group_id" in resp["error"]


def test_group_assign_missing_ids():
    req = DummyRequest(method="POST", json={"group_id": 1})
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_assign_subscriber(req))
    assert status == 400
    assert "Missing group_id or subscriber_id" in resp["error"]


def test_group_subscribers_calls_client(monkeypatch):
    monkeypatch.setattr(
        groups_api,
        "groups_client",
        types.SimpleNamespace(subscribers=lambda group_id, params=None: {"id": group_id}),
    )
    req = DummyRequest(method="GET", args={"group_id": "7"})
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_subscribers(req))
    assert status == 200
    assert resp["id"] == "7"


def test_group_unassign_missing_ids():
    req = DummyRequest(method="DELETE", json={"group_id": 1})
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_unassign_subscriber(req))
    assert status == 400
    assert "Missing group_id or subscriber_id" in resp["error"]


def test_group_unassign_calls_client(monkeypatch):
    monkeypatch.setattr(
        groups_api,
        "groups_client",
        types.SimpleNamespace(unassign_subscriber=lambda subscriber_id, group_id: {"ok": True}),
    )
    req = DummyRequest(method="DELETE", json={"group_id": 1, "subscriber_id": 2})
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_unassign_subscriber(req))
    assert status == 200
    assert resp["ok"] is True


def test_groups_invalid_method():
    req = DummyRequest(method="PATCH")
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(req))
    assert status == 405


def test_group_subscribers_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_subscribers(req))
    assert status == 405


def test_group_assign_invalid_method():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_assign_subscriber(req))
    assert status == 405


def test_group_unassign_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(groups_api.admin_mailerlite_group_unassign_subscriber(req))
    assert status == 405


def test_groups_mailerlite_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise groups_api.MailerLiteError("boom", status=500, payload={"detail": "x"})

    monkeypatch.setattr(
        groups_api,
        "groups_client",
        types.SimpleNamespace(list=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(req))
    assert status == 500
    assert resp["error"] == "MailerLite request failed"
