import types

from api.admin import newsletter_api
from tests.utils import DummyRequest, unwrap_response


def test_admin_get_newsletter_signups_invalid_method():
    """Rejects invalid method."""
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_signups(req))
    assert status == 405
    assert resp["error"] == "Invalid request method"


def test_admin_get_newsletter_signups_by_id(monkeypatch):
    """Fetches signup by id."""
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(get_by_id=lambda signup_id: ({"signup": {"id": signup_id}}, 200)),
    )
    req = DummyRequest(method="GET", args={"id": "signup-1"})
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_signups(req))
    assert status == 200
    assert resp["signup"]["id"] == "signup-1"


def test_admin_get_newsletter_signups_all(monkeypatch):
    """Fetches all signups."""
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(get_all=lambda: ({"signups": []}, 200)),
    )
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_signups(req))
    assert status == 200
    assert resp == {"signups": []}


def test_admin_update_newsletter_signup_missing_id():
    """Returns 400 when id is missing."""
    req = DummyRequest(method="PUT", json={"active": False})
    resp, status = unwrap_response(newsletter_api.admin_update_newsletter_signup(req))
    assert status == 400
    assert resp["error"] == "Missing signup ID"


def test_admin_update_newsletter_signup_happy_path(monkeypatch):
    """Updates signup via service."""
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(update=lambda signup_id, data: ({"message": "ok"}, 200)),
    )
    req = DummyRequest(method="PUT", json={"id": "signup-1", "active": False})
    resp, status = unwrap_response(newsletter_api.admin_update_newsletter_signup(req))
    assert status == 200
    assert resp["message"] == "ok"


def test_admin_delete_newsletter_signup_missing_id():
    """Returns 400 when id is missing."""
    req = DummyRequest(method="DELETE", args={})
    resp, status = unwrap_response(newsletter_api.admin_delete_newsletter_signup(req))
    assert status == 400
    assert resp["error"] == "Missing signup ID"


def test_admin_delete_newsletter_signup_happy_path(monkeypatch):
    """Deletes signup via service."""
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(delete=lambda signup_id: ({"message": "ok"}, 200)),
    )
    req = DummyRequest(method="DELETE", args={"id": "signup-1"})
    resp, status = unwrap_response(newsletter_api.admin_delete_newsletter_signup(req))
    assert status == 200
    assert resp["message"] == "ok"
