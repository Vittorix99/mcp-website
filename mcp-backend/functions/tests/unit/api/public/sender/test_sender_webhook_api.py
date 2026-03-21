from unittest.mock import patch

import pytest

from api.public import sender_webhook_api
from tests.utils import DummyRequest, unwrap_response


@pytest.fixture(autouse=True)
def _disable_webhook_secret_by_default(monkeypatch):
    # Keep tests deterministic even if .env config sets SENDER_WEBHOOK_SECRET.
    monkeypatch.setattr(sender_webhook_api, "SENDER_WEBHOOK_SECRET", None)


class TestSenderWebhook:
    """Unit tests for Sender webhook endpoint behavior."""

    def test_non_post_returns_405(self):
        req = DummyRequest(method="GET", json={})
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))
        assert status == 405

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_unsubscribed_event_marks_inactive(self, MockRepo):
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {"email": "x@test.com"}},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        assert resp == {"received": True}
        mock_repo.unsubscribe_by_email.assert_called_once_with("x@test.com")

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_bounced_event_marks_inactive(self, MockRepo):
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.bounced", "data": {"email": "x@test.com"}},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        mock_repo.unsubscribe_by_email.assert_called_once_with("x@test.com")

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_spam_event_marks_inactive(self, MockRepo):
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.spam_reported", "data": {"email": "x@test.com"}},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        mock_repo.unsubscribe_by_email.assert_called_once_with("x@test.com")

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_unknown_event_returns_200_no_action(self, MockRepo):
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "something.else", "data": {"email": "x@test.com"}},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        assert resp == {"received": True}
        mock_repo.unsubscribe_by_email.assert_not_called()

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_missing_email_returns_200_gracefully(self, MockRepo):
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {}},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        mock_repo.unsubscribe_by_email.assert_not_called()

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_valid_webhook_secret_accepted(self, MockRepo, monkeypatch):
        monkeypatch.setattr(sender_webhook_api, "SENDER_WEBHOOK_SECRET", "abc")
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {"email": "x@test.com"}},
            headers={"X-Sender-Token": "abc"},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        mock_repo.unsubscribe_by_email.assert_called_once_with("x@test.com")

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_invalid_webhook_secret_returns_403(self, MockRepo, monkeypatch):
        monkeypatch.setattr(sender_webhook_api, "SENDER_WEBHOOK_SECRET", "abc")

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {"email": "x@test.com"}},
            headers={"X-Sender-Token": "wrong"},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 403
        assert resp["error"] == "Unauthorized"
        MockRepo.return_value.unsubscribe_by_email.assert_not_called()

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_no_secret_configured_skips_auth(self, MockRepo, monkeypatch):
        monkeypatch.setattr(sender_webhook_api, "SENDER_WEBHOOK_SECRET", None)
        mock_repo = MockRepo.return_value

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {"email": "x@test.com"}},
            headers={},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        mock_repo.unsubscribe_by_email.assert_called_once_with("x@test.com")

    @patch("api.public.sender_webhook_api.NewsletterRepository")
    def test_always_returns_200_on_internal_error(self, MockRepo):
        mock_repo = MockRepo.return_value
        mock_repo.unsubscribe_by_email.side_effect = Exception("db down")

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {"email": "x@test.com"}},
        )
        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        assert resp == {"received": True}
