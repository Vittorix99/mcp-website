import types

from api.admin import error_logs_api
from tests.utils import DummyRequest, unwrap_response


def test_admin_error_logs_invalid_method():
    req = DummyRequest(method="PATCH")
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 405
    assert resp["error"] == "Invalid request method"


def test_admin_error_logs_get_list(monkeypatch):
    monkeypatch.setattr(
        error_logs_api,
        "error_logs_service",
        types.SimpleNamespace(list_logs=lambda limit=100, service=None, resolved=None: [{"id": "e1"}]),
    )
    req = DummyRequest(method="GET", args={"limit": "10", "service": "Pass2U", "resolved": "false"})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 200
    assert resp == {"error_logs": [{"id": "e1"}]}


def test_admin_error_logs_get_by_id_not_found(monkeypatch):
    monkeypatch.setattr(
        error_logs_api,
        "error_logs_service",
        types.SimpleNamespace(get_log=lambda _id: None),
    )
    req = DummyRequest(method="GET", args={"id": "missing"})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 404
    assert resp["error"] == "Error log not found"


def test_admin_error_logs_post_missing_fields_400():
    req = DummyRequest(method="POST", json={"service": "Pass2U"})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 400
    assert resp["error"] == "Missing message"


def test_admin_error_logs_post_success(monkeypatch):
    monkeypatch.setattr(
        error_logs_api,
        "error_logs_service",
        types.SimpleNamespace(create_log=lambda payload: {"id": "e2", **payload}),
    )
    req = DummyRequest(method="POST", json={"service": "Sender", "message": "boom"})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 201
    assert resp["id"] == "e2"
    assert resp["service"] == "Sender"


def test_admin_error_logs_put_missing_id_400():
    req = DummyRequest(method="PUT", json={"message": "x"})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 400
    assert resp["error"] == "Missing id"


def test_admin_error_logs_put_not_found(monkeypatch):
    monkeypatch.setattr(
        error_logs_api,
        "error_logs_service",
        types.SimpleNamespace(update_log=lambda error_log_id, payload: None),
    )
    req = DummyRequest(method="PUT", json={"id": "missing", "resolved": True})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 404
    assert resp["error"] == "Error log not found"


def test_admin_error_logs_delete_missing_id_400():
    req = DummyRequest(method="DELETE", args={})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 400
    assert resp["error"] == "Missing id"


def test_admin_error_logs_delete_success(monkeypatch):
    monkeypatch.setattr(
        error_logs_api,
        "error_logs_service",
        types.SimpleNamespace(delete_log=lambda error_log_id: True),
    )
    req = DummyRequest(method="DELETE", args={"id": "e1"})
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 200
    assert resp == {"deleted": True}
