import types

from dto.newsletter_api import (
    NewsletterActionResponseDTO,
    NewsletterConsentResponseDTO,
    NewsletterConsentsListResponseDTO,
    NewsletterSignupEnvelopeResponseDTO,
    NewsletterSignupResponseDTO,
    NewsletterSignupsListResponseDTO,
)
from api.admin import newsletter_api
from tests.utils import DummyRequest, unwrap_response


def test_admin_get_newsletter_signups_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_signups(req))
    assert status == 405
    assert resp["error"] == "Invalid method"


def test_admin_get_newsletter_signups_by_id(monkeypatch):
    captured = {}

    def get_by_id(signup_id):
        captured["id"] = signup_id
        return NewsletterSignupEnvelopeResponseDTO(
            signup=NewsletterSignupResponseDTO(id=signup_id, email="user@example.com")
        )

    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(get_signup_by_id=get_by_id),
    )
    req = DummyRequest(method="GET", args={"id": "signup-1"})
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_signups(req))
    assert status == 200
    assert captured["id"] == "signup-1"
    assert resp["signup"]["id"] == "signup-1"


def test_admin_get_newsletter_signups_all(monkeypatch):
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(get_all_signups=lambda: NewsletterSignupsListResponseDTO(signups=[])),
    )
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_signups(req))
    assert status == 200
    assert resp == {"signups": []}


def test_admin_update_newsletter_signup_invalid_data_does_not_call_service(monkeypatch):
    called = False

    def update(_dto):
        nonlocal called
        called = True

    monkeypatch.setattr(newsletter_api, "newsletter_service", types.SimpleNamespace(update_signup=update))
    resp, status = unwrap_response(
        newsletter_api.admin_update_newsletter_signup(DummyRequest(method="PUT", json={"active": False}))
    )
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_admin_update_newsletter_signup_happy_path(monkeypatch):
    captured = {}

    def update(dto):
        captured["dto"] = dto
        return NewsletterActionResponseDTO(message="ok")

    monkeypatch.setattr(newsletter_api, "newsletter_service", types.SimpleNamespace(update_signup=update))
    req = DummyRequest(method="PUT", json={"id": "signup-1", "active": False})
    resp, status = unwrap_response(newsletter_api.admin_update_newsletter_signup(req))
    assert status == 200
    assert resp["message"] == "ok"
    assert captured["dto"].id == "signup-1"
    assert captured["dto"].active is False


def test_admin_delete_newsletter_signup_invalid_data_does_not_call_service(monkeypatch):
    called = False

    def delete(_signup_id):
        nonlocal called
        called = True

    monkeypatch.setattr(newsletter_api, "newsletter_service", types.SimpleNamespace(delete_signup=delete))
    resp, status = unwrap_response(newsletter_api.admin_delete_newsletter_signup(DummyRequest(method="DELETE", args={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_admin_delete_newsletter_signup_happy_path(monkeypatch):
    captured = {}

    def delete(signup_id):
        captured["id"] = signup_id
        return NewsletterActionResponseDTO(message="ok")

    monkeypatch.setattr(newsletter_api, "newsletter_service", types.SimpleNamespace(delete_signup=delete))
    req = DummyRequest(method="DELETE", args={"id": "signup-1"})
    resp, status = unwrap_response(newsletter_api.admin_delete_newsletter_signup(req))
    assert status == 200
    assert resp["message"] == "ok"
    assert captured["id"] == "signup-1"


def test_admin_get_newsletter_consents_happy_path(monkeypatch):
    monkeypatch.setattr(
        newsletter_api,
        "newsletter_service",
        types.SimpleNamespace(
            get_all_consents=lambda: NewsletterConsentsListResponseDTO(
                consents=[NewsletterConsentResponseDTO(id="consent-1", email="user@example.com")]
            )
        ),
    )
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(newsletter_api.admin_get_newsletter_consents(req))
    assert status == 200
    assert resp["consents"][0]["id"] == "consent-1"
