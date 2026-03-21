import types

from api.admin.sender import campaigns_api
from tests.utils import DummyRequest, unwrap_response


class TestAdminSenderCampaigns:
    """Unit tests for admin_sender_campaigns handler."""

    def test_get_list(self, monkeypatch):
        svc = types.SimpleNamespace(list_campaigns=lambda params=None: {"data": []})
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="GET", args={})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 200
        assert resp == {"data": []}

    def test_get_single_by_id(self, monkeypatch):
        svc = types.SimpleNamespace(get_campaign=lambda campaign_id: {"id": campaign_id})
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="GET", args={"id": "X"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 200
        assert resp["id"] == "X"

    def test_post_creates(self, monkeypatch):
        called = {}

        def _create_campaign(**kwargs):
            called.update(kwargs)
            return {"id": "new-camp"}

        svc = types.SimpleNamespace(create_campaign=_create_campaign)
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(
            method="POST",
            json={
                "title": "Camp",
                "subject": "Sub",
                "from_name": "MCP",
                "from_email": "info@test.com",
                "content_html": "<p>Hello</p>",
                "groups": ["g1"],
            },
        )
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 200
        assert resp == {"id": "new-camp"}
        assert called["title"] == "Camp"
        assert called["groups"] == ["g1"]

    def test_post_missing_fields_400(self):
        req = DummyRequest(method="POST", json={"title": "Camp"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 400
        assert "error" in resp

    def test_put_updates(self, monkeypatch):
        called = {}

        def _update_campaign(**kwargs):
            called.update(kwargs)
            return {"updated": True}

        svc = types.SimpleNamespace(update_campaign=_update_campaign)
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="PUT", json={"id": "camp-1", "subject": "New"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 200
        assert resp == {"updated": True}
        assert called["campaign_id"] == "camp-1"

    def test_put_missing_id_400(self):
        req = DummyRequest(method="PUT", json={"subject": "New"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 400
        assert resp["error"] == "Missing campaign_id"

    def test_delete_not_implemented_501(self, monkeypatch):
        svc = types.SimpleNamespace(delete_campaign=lambda campaign_id: False)
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="DELETE", json={"id": "camp-1"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

        assert status == 501
        assert "error" in resp


class TestAdminSenderCampaignSend:
    """Unit tests for admin_sender_campaign_send handler."""

    def test_sends_ok_returns_200(self, monkeypatch):
        svc = types.SimpleNamespace(send_campaign=lambda campaign_id: (True, None))
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="POST", json={"id": "camp-1"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_send(req))

        assert status == 200
        assert resp == {"sent": True}

    def test_sender_error_returns_422(self, monkeypatch):
        svc = types.SimpleNamespace(send_campaign=lambda campaign_id: (False, "Unsubscribe link: missing"))
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="POST", json={"id": "camp-1"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_send(req))

        assert status == 422
        assert resp["sent"] is False
        assert "Unsubscribe" in resp["error"]

    def test_missing_id_400(self):
        req = DummyRequest(method="POST", json={})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_send(req))

        assert status == 400
        assert resp["error"] == "Missing campaign_id"

    def test_only_post_allowed(self):
        req = DummyRequest(method="GET", json={})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_send(req))

        assert status == 405


class TestAdminSenderCampaignSchedule:
    """Unit tests for admin_sender_campaign_schedule handler."""

    def test_schedules_ok(self, monkeypatch):
        svc = types.SimpleNamespace(schedule_campaign=lambda campaign_id, scheduled_at: (True, None))
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="POST", json={"id": "camp-1", "scheduled_at": "2025-06-15T20:00:00Z"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_schedule(req))

        assert status == 200
        assert resp == {"scheduled": True}

    def test_schedule_error_422(self, monkeypatch):
        svc = types.SimpleNamespace(schedule_campaign=lambda campaign_id, scheduled_at: (False, "msg"))
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="POST", json={"id": "camp-1", "scheduled_at": "2025-06-15T20:00:00Z"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_schedule(req))

        assert status == 422
        assert resp == {"scheduled": False, "error": "msg"}

    def test_cancel_schedule_delete(self, monkeypatch):
        called = {}

        def _cancel(campaign_id):
            called["id"] = campaign_id
            return True

        svc = types.SimpleNamespace(cancel_scheduled_campaign=_cancel)
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="DELETE", json={"id": "camp-1"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_schedule(req))

        assert status == 200
        assert resp == {"cancelled": True}
        assert called["id"] == "camp-1"

    def test_missing_id_or_date_400(self):
        req = DummyRequest(method="POST", json={"id": "camp-1"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_schedule(req))

        assert status == 400
        assert resp["error"] == "Missing campaign_id or scheduled_at"


class TestAdminSenderCampaignStats:
    """Unit tests for admin_sender_campaign_stats handler."""

    def test_opens_type(self, monkeypatch):
        svc = types.SimpleNamespace(get_campaign_opens=lambda campaign_id: {"data": ["o"]})
        svc.get_campaign_clicks = lambda campaign_id: {"data": []}
        svc.get_campaign_unsubscribes = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_hard = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_soft = lambda campaign_id: {"data": []}
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="GET", args={"id": "camp-1", "type": "opens"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

        assert status == 200
        assert resp == {"data": ["o"]}

    def test_clicks_type(self, monkeypatch):
        svc = types.SimpleNamespace(get_campaign_opens=lambda campaign_id: {"data": []})
        svc.get_campaign_clicks = lambda campaign_id: {"data": ["c"]}
        svc.get_campaign_unsubscribes = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_hard = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_soft = lambda campaign_id: {"data": []}
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="GET", args={"id": "camp-1", "type": "clicks"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

        assert status == 200
        assert resp == {"data": ["c"]}

    def test_bounces_hard(self, monkeypatch):
        svc = types.SimpleNamespace(get_campaign_opens=lambda campaign_id: {"data": []})
        svc.get_campaign_clicks = lambda campaign_id: {"data": []}
        svc.get_campaign_unsubscribes = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_hard = lambda campaign_id: {"data": ["b"]}
        svc.get_campaign_bounces_soft = lambda campaign_id: {"data": []}
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="GET", args={"id": "camp-1", "type": "bounces_hard"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

        assert status == 200
        assert resp == {"data": ["b"]}

    def test_unknown_type_400(self, monkeypatch):
        svc = types.SimpleNamespace(get_campaign_opens=lambda campaign_id: {"data": []})
        svc.get_campaign_clicks = lambda campaign_id: {"data": []}
        svc.get_campaign_unsubscribes = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_hard = lambda campaign_id: {"data": []}
        svc.get_campaign_bounces_soft = lambda campaign_id: {"data": []}
        monkeypatch.setattr(campaigns_api, "get_sender_service", lambda: svc)

        req = DummyRequest(method="GET", args={"id": "camp-1", "type": "invalid"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

        assert status == 400
        assert "Unknown stat type" in resp["error"]

    def test_missing_id_400(self):
        req = DummyRequest(method="GET", args={"type": "opens"})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

        assert status == 400
        assert resp["error"] == "Missing campaign_id"

    def test_only_get_allowed(self):
        req = DummyRequest(method="POST", json={})
        resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

        assert status == 405
