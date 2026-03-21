from unittest.mock import MagicMock, patch

from api.public import sender_webhook_api
from services.sender.sender_service import SenderService
from tests.utils import DummyRequest, unwrap_response


def _response(status_code, payload):
    resp = MagicMock()
    resp.status_code = status_code
    if payload is None:
        resp.content = b""
        resp.json.side_effect = ValueError("no json")
    else:
        resp.content = b"x"
        resp.json.return_value = payload
    return resp


class TestCreateCampaignIntegration:
    """Integration tests for create campaign through service + routes + HTTP layer."""

    @patch("routes.sender_routes.requests.request")
    def test_full_create_flow(self, mock_request):
        mock_request.return_value = _response(201, {"data": {"id": "camp-1"}})
        svc = SenderService("test-key")

        result = svc.create_campaign(
            title="Camp",
            subject="Sub",
            from_name="MCP",
            from_email="info@test.com",
            content_html="<p>Hello</p>",
        )

        assert result == {"data": {"id": "camp-1"}}

    def test_create_missing_api_key(self):
        svc = SenderService(api_key=None)
        svc._api_key = None

        result = svc.create_campaign(
            title="Camp",
            subject="Sub",
            from_name="MCP",
            from_email="info@test.com",
            content_html="<p>Hello</p>",
        )

        assert result is None


class TestSendCampaignIntegration:
    """Integration tests for campaign send flow through HTTP wrapper."""

    @patch("routes.sender_routes.requests.request")
    def test_send_success_200(self, mock_request):
        mock_request.return_value = _response(200, {"sent": True})
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-1")

        assert ok is True
        assert err is None

    @patch("routes.sender_routes.requests.request")
    def test_send_unsubscribe_error(self, mock_request):
        payload = {"error": [{"title": "Unsubscribe link", "details": "Insert <a href=..."}]}
        mock_request.return_value = _response(422, payload)
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-1")

        assert ok is False
        assert "Unsubscribe link" in err

    @patch("routes.sender_routes.requests.request")
    def test_send_dmarc_error(self, mock_request):
        payload = {"error": [{"title": "DMARC record", "details": "domain not set up"}]}
        mock_request.return_value = _response(422, payload)
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-1")

        assert ok is False
        assert err == "DMARC record: domain not set up"

    @patch("routes.sender_routes.requests.request")
    def test_send_multiple_errors(self, mock_request):
        payload = {
            "error": [
                {"title": "Unsubscribe link", "details": "missing"},
                {"title": "DMARC record", "details": "missing"},
            ]
        }
        mock_request.return_value = _response(422, payload)
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-1")

        assert ok is False
        assert err == "Unsubscribe link: missing | DMARC record: missing"


class TestScheduleCampaignIntegration:
    """Integration tests for schedule campaign flow through HTTP wrapper."""

    @patch("routes.sender_routes.requests.request")
    def test_schedule_iso_to_sender_format(self, mock_request):
        mock_request.return_value = _response(200, {"scheduled": True})
        svc = SenderService("test-key")

        ok, err = svc.schedule_campaign("camp-1", "2025-12-01T18:30:00Z")

        assert ok is True
        assert err is None
        sent_json = mock_request.call_args.kwargs["json"]
        assert sent_json["schedule_time"] == "2025-12-01 18:30:00"

    @patch("routes.sender_routes.requests.request")
    def test_schedule_failure_422(self, mock_request):
        mock_request.return_value = _response(422, {"error": [{"title": "Invalid time", "details": "past"}]})
        svc = SenderService("test-key")

        ok, err = svc.schedule_campaign("camp-1", "2025-12-01T18:30:00Z")

        assert ok is False
        assert err == "Invalid time: past"


class TestUpsertSubscriberIntegration:
    """Integration tests for subscriber/group service methods with HTTP mocked."""

    @patch("routes.sender_routes.requests.request")
    def test_upsert_new_subscriber(self, mock_request):
        mock_request.return_value = _response(200, {"data": {"id": "sub-1"}})
        svc = SenderService("test-key")

        result = svc.upsert_subscriber("x@test.com", groups=["g1"])

        assert result == {"data": {"id": "sub-1"}}

    @patch("routes.sender_routes.requests.request")
    def test_upsert_existing_subscriber_200(self, mock_request):
        mock_request.return_value = _response(200, {"data": {"id": "sub-1", "updated": True}})
        svc = SenderService("test-key")

        result = svc.upsert_subscriber("x@test.com")

        assert result == {"data": {"id": "sub-1", "updated": True}}

    @patch("routes.sender_routes.requests.request")
    def test_add_to_group(self, mock_request):
        mock_request.return_value = _response(200, {"ok": True})
        svc = SenderService("test-key")

        ok = svc.add_to_group("x@test.com", "g1")

        assert ok is True

    @patch("routes.sender_routes.requests.request")
    def test_remove_from_group(self, mock_request):
        mock_request.return_value = _response(200, {"ok": True})
        svc = SenderService("test-key")

        ok = svc.remove_from_group("x@test.com", "g1")

        assert ok is True


class TestWebhookIntegration:
    """Integration-style test for webhook -> repository unsubscribe flow."""

    def test_end_to_end_unsubscribe(self, monkeypatch):
        import repositories.newsletter_repository as newsletter_repo_module

        signup_doc = MagicMock()
        consent_doc = MagicMock()

        signups_collection = MagicMock()
        consents_collection = MagicMock()
        signups_collection.where.return_value.stream.return_value = [signup_doc]
        consents_collection.where.return_value.stream.return_value = [consent_doc]

        fake_db = MagicMock()
        fake_db.collection.side_effect = lambda name: signups_collection if name == "newsletter_signups" else consents_collection

        monkeypatch.setattr(newsletter_repo_module, "db", fake_db)
        monkeypatch.setattr(sender_webhook_api, "SENDER_WEBHOOK_SECRET", None)

        req = DummyRequest(
            method="POST",
            json={"event": "subscriber.unsubscribed", "data": {"email": "x@t.com"}},
            headers={},
        )

        resp, status = unwrap_response(sender_webhook_api.sender_webhook(req))

        assert status == 200
        assert resp == {"received": True}
        signup_doc.reference.update.assert_called_once_with({"active": False})
        consent_doc.reference.update.assert_called_once_with({"active": False})
