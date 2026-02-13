import types

from api.public import newsletter_api
from tests.utils import DummyRequest, unwrap_response


def test_newsletter_signup_invalid_method():
    """Rejects invalid method."""
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(newsletter_api.newsletter_signup(req))
    assert status == 405
    assert resp["error"] == "Invalid request method"


def test_newsletter_signup_missing_email():
    """Returns 400 when email is missing."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(newsletter_api.newsletter_signup(req))
    assert status == 400
    assert resp["error"] == "Missing email"


def test_newsletter_signup_happy_path(monkeypatch):
    """Delegates signup to service."""
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(signup=lambda data: ({"message": "ok"}, 200)),
    )
    req = DummyRequest(method="POST", json={"email": "user@example.com"})
    resp, status = unwrap_response(newsletter_api.newsletter_signup(req))
    assert status == 200
    assert resp["message"] == "ok"


def test_newsletter_participants_invalid_method():
    """Rejects invalid method."""
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(newsletter_api.newsletter_participants(req))
    assert status == 405
    assert resp["error"] == "Invalid request method"


def test_newsletter_participants_missing_body():
    """Returns 400 when participants are missing."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(newsletter_api.newsletter_participants(req))
    assert status == 400
    assert resp["error"] == "Missing participants"


def test_newsletter_participants_happy_path(monkeypatch):
    """Delegates bulk add to service."""
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(add_participants=lambda participants: ({"message": "ok"}, 200)),
    )
    req = DummyRequest(method="POST", json={"participants": [{"email": "user@example.com"}]})
    resp, status = unwrap_response(newsletter_api.newsletter_participants(req))
    assert status == 200
    assert resp["message"] == "ok"
