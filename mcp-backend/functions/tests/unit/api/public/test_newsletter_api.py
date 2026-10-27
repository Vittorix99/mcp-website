import types

from api.public import newsletter_api
from dto.newsletter_api import NewsletterActionResponseDTO
from tests.utils import DummyRequest, unwrap_response


def test_newsletter_signup_invalid_method():
    resp, status = unwrap_response(newsletter_api.newsletter_signup(DummyRequest(method="GET")))
    assert status == 405
    assert resp["error"] == "Invalid method"


def test_newsletter_signup_missing_email_does_not_call_service(monkeypatch):
    called = False

    def signup(_dto):
        nonlocal called
        called = True

    monkeypatch.setattr(newsletter_api, "newsletter_service", types.SimpleNamespace(signup=signup))
    resp, status = unwrap_response(newsletter_api.newsletter_signup(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_newsletter_signup_happy_path(monkeypatch):
    captured = {}

    def signup(dto):
        captured["dto"] = dto
        return NewsletterActionResponseDTO(message="ok")

    monkeypatch.setattr(newsletter_api, "newsletter_service", types.SimpleNamespace(signup=signup))
    monkeypatch.setattr(newsletter_api, "sync_newsletter_signup_to_sender", lambda **_kwargs: None)
    req = DummyRequest(method="POST", json={"email": "user@example.com", "name": "User"})
    resp, status = unwrap_response(newsletter_api.newsletter_signup(req))
    assert status == 200
    assert resp["message"] == "ok"
    assert str(captured["dto"].email) == "user@example.com"
    assert captured["dto"].name == "User"
