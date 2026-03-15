from types import SimpleNamespace

import pytest

import services.sender.sender_service as sender_service_module
from routes.sender_routes import SenderApiResult
from services.sender.sender_service import SenderService, _format_sender_error


class TestSenderServiceInit:
    """Unit tests for SenderService initialization and API key resolution."""

    def test_no_api_key_raises_on_use(self):
        svc = SenderService(api_key=None)
        svc._api_key = None
        with pytest.raises(RuntimeError):
            svc._key()

    def test_api_key_from_constructor(self):
        svc = SenderService("mykey")
        assert svc._key() == "mykey"

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setattr(sender_service_module, "SENDER_API_KEY", "envkey")
        svc = SenderService()
        assert svc._key() == "envkey"


class TestFormatSenderError:
    """Unit tests for Sender error payload formatting."""

    def test_array_error_format(self):
        payload = {"error": [{"title": "X", "details": "Y"}]}
        assert _format_sender_error(payload, 422) == "X: Y"

    def test_multiple_errors_joined(self):
        payload = {
            "error": [
                {"title": "X", "details": "Y"},
                {"title": "A", "details": "B"},
            ]
        }
        assert _format_sender_error(payload, 422) == "X: Y | A: B"

    def test_string_error(self):
        payload = {"error": "plain string"}
        assert _format_sender_error(payload, 422) == "plain string"

    def test_unknown_format(self):
        assert _format_sender_error({}, 422) == "HTTP 422"

    def test_non_dict_payload(self):
        assert _format_sender_error("raw", 500) == "HTTP 500"


class TestUpsertSubscriber:
    """Unit tests for subscriber upsert behavior in SenderService."""

    def test_success_returns_dict(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "upsert_subscriber",
            lambda api_key, body: SenderApiResult(200, {"data": {"id": "sub-1"}}),
        )
        svc = SenderService("test-key")

        result = svc.upsert_subscriber("x@test.com")

        assert result == {"data": {"id": "sub-1"}}

    def test_failure_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "upsert_subscriber",
            lambda api_key, body: SenderApiResult(422, {"error": "bad"}, "bad"),
        )
        svc = SenderService("test-key")

        assert svc.upsert_subscriber("x@test.com") is None

    def test_passes_groups_to_route(self, monkeypatch):
        captured = {}

        def _fake(api_key, body):
            captured["api_key"] = api_key
            captured["body"] = body
            return SenderApiResult(200, {"ok": True})

        monkeypatch.setattr(sender_service_module.SenderRoutes, "upsert_subscriber", _fake)
        svc = SenderService("test-key")

        svc.upsert_subscriber("x@test.com", groups=["g1"])

        assert captured["api_key"] == "test-key"
        assert captured["body"]["email"] == "x@test.com"
        assert captured["body"]["groups"] == ["g1"]

    def test_exception_returns_none(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise Exception("network")

        monkeypatch.setattr(sender_service_module.SenderRoutes, "upsert_subscriber", _boom)
        svc = SenderService("test-key")

        assert svc.upsert_subscriber("x@test.com") is None


class TestSendCampaign:
    """Unit tests for send_campaign tuple contract."""

    def test_success_returns_true_none(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "send_campaign",
            lambda api_key, campaign_id: SenderApiResult(200, {"sent": True}),
        )
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-123")

        assert ok is True
        assert err is None

    def test_sender_error_422(self, monkeypatch):
        payload = {"error": [{"title": "T", "details": "D"}]}
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "send_campaign",
            lambda api_key, campaign_id: SenderApiResult(422, payload),
        )
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-123")

        assert ok is False
        assert err == "T: D"

    def test_sender_error_403_unsubscribe_missing(self, monkeypatch):
        payload = {"error": [{"title": "Unsubscribe link", "details": "Insert this code"}]}
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "send_campaign",
            lambda api_key, campaign_id: SenderApiResult(403, payload),
        )
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-123")

        assert ok is False
        assert "unsubscribe" in err.lower()

    def test_exception_returns_false_error(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise Exception("kaboom")

        monkeypatch.setattr(sender_service_module.SenderRoutes, "send_campaign", _boom)
        svc = SenderService("test-key")

        ok, err = svc.send_campaign("camp-123")

        assert ok is False
        assert "kaboom" in err


class TestScheduleCampaign:
    """Unit tests for schedule_campaign conversion and errors."""

    def test_iso_converted_to_sender_format(self, monkeypatch):
        captured = {}

        def _fake(api_key, campaign_id, schedule_time):
            captured["schedule_time"] = schedule_time
            return SenderApiResult(200, {"scheduled": True})

        monkeypatch.setattr(sender_service_module.SenderRoutes, "schedule_campaign", _fake)
        svc = SenderService("test-key")

        ok, err = svc.schedule_campaign("camp-123", "2025-06-15T20:00:00Z")

        assert ok is True
        assert err is None
        assert captured["schedule_time"] == "2025-06-15 20:00:00"

    def test_iso_with_timezone_offset(self, monkeypatch):
        captured = {}

        def _fake(api_key, campaign_id, schedule_time):
            captured["schedule_time"] = schedule_time
            return SenderApiResult(200, {"scheduled": True})

        monkeypatch.setattr(sender_service_module.SenderRoutes, "schedule_campaign", _fake)
        svc = SenderService("test-key")

        ok, err = svc.schedule_campaign("camp-123", "2025-06-15T22:00:00+02:00")

        assert ok is True
        assert err is None
        assert captured["schedule_time"] == "2025-06-15 20:00:00"

    def test_invalid_iso_returns_false_error(self):
        svc = SenderService("test-key")

        ok, err = svc.schedule_campaign("camp-123", "not-a-date")

        assert ok is False
        assert err

    def test_sender_422_returns_false_error(self, monkeypatch):
        payload = {"error": [{"title": "Invalid time", "details": "past"}]}
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "schedule_campaign",
            lambda api_key, campaign_id, schedule_time: SenderApiResult(422, payload),
        )
        svc = SenderService("test-key")

        ok, err = svc.schedule_campaign("camp-123", "2025-06-15T20:00:00Z")

        assert ok is False
        assert err == "Invalid time: past"


class TestGetCampaignStats:
    """Unit tests for campaign stats accessors."""

    def test_opens_returns_dict(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "get_campaign_opens",
            lambda api_key, campaign_id: SenderApiResult(200, {"data": [1]}),
        )
        svc = SenderService("test-key")

        assert svc.get_campaign_opens("camp-1") == {"data": [1]}

    def test_clicks_returns_none_on_error(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "get_campaign_clicks",
            lambda api_key, campaign_id: SenderApiResult(500, {"error": "boom"}),
        )
        svc = SenderService("test-key")

        assert svc.get_campaign_clicks("camp-1") is None

    def test_404_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "get_campaign_opens",
            lambda api_key, campaign_id: SenderApiResult(404, {"error": "not found"}),
        )
        svc = SenderService("test-key")

        assert svc.get_campaign_opens("camp-1") is None


class TestDeleteCampaign:
    """Unit tests for delete_campaign boolean contract."""

    def test_success_returns_true(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "delete_campaign",
            lambda api_key, campaign_id: SenderApiResult(200, {"deleted": True}),
        )
        svc = SenderService("test-key")

        assert svc.delete_campaign("camp-1") is True

    def test_failure_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "delete_campaign",
            lambda api_key, campaign_id: SenderApiResult(422, {"error": "bad"}),
        )
        svc = SenderService("test-key")

        assert svc.delete_campaign("camp-1") is False


class TestGroupHelpers:
    """Unit tests for list/create group behavior in SenderService."""

    def test_list_groups_returns_payload(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "list_groups",
            lambda api_key: SenderApiResult(200, {"data": [{"id": "1", "title": "Newsletter"}]}),
        )
        svc = SenderService("test-key")

        payload = svc.list_groups()

        assert payload == {"data": [{"id": "1", "title": "Newsletter"}]}

    def test_create_group_returns_none_on_failure(self, monkeypatch):
        monkeypatch.setattr(
            sender_service_module.SenderRoutes,
            "create_group",
            lambda api_key, title: SenderApiResult(500, {"error": "boom"}),
        )
        svc = SenderService("test-key")

        assert svc.create_group("Newsletter") is None
