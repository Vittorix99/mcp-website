import requests
from unittest.mock import MagicMock, patch

import pytest

from clients.sender_client import SenderApiResult, SenderRoutes


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


class TestSenderApiResult:
    """Unit tests for SenderApiResult dataclass behavior."""

    @pytest.mark.parametrize("status", [200, 201, 204])
    def test_ok_true_for_2xx(self, status):
        assert SenderApiResult(status_code=status).ok is True

    @pytest.mark.parametrize("status", [400, 422, 500])
    def test_ok_false_for_non_2xx(self, status):
        assert SenderApiResult(status_code=status).ok is False

    def test_error_message_preserved(self):
        result = SenderApiResult(status_code=400, error_message="X")
        assert result.error_message == "X"


class TestUpsertSubscriber:
    """Unit tests for subscriber routes."""

    @patch("routes.sender_routes.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = _response(200, {"data": {"id": "sub-1"}})

        result = SenderRoutes.upsert_subscriber("test-key", {"email": "x@test.com", "groups": ["g1"]})

        assert result.status_code == 200
        assert result.payload == {"data": {"id": "sub-1"}}
        assert result.ok is True

    @patch("routes.sender_routes.requests.request")
    def test_401_unauthorized(self, mock_request):
        mock_request.return_value = _response(401, {"error": "Unauthorized"})

        result = SenderRoutes.upsert_subscriber("bad-key", {"email": "x@test.com"})

        assert result.status_code == 401
        assert result.ok is False
        assert result.error_message == "Unauthorized"

    @patch("routes.sender_routes.requests.request", side_effect=requests.Timeout("timeout"))
    def test_request_timeout(self, _mock_request):
        with pytest.raises(requests.Timeout):
            SenderRoutes.upsert_subscriber("test-key", {"email": "x@test.com"})


class TestCampaignRoutes:
    """Unit tests for campaign routes and URLs."""

    @patch("routes.sender_routes.requests.request")
    def test_send_campaign_post_correct_url(self, mock_request):
        mock_request.return_value = _response(200, {"sent": True})

        SenderRoutes.send_campaign("test-key", "camp-123")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "POST"
        assert kwargs["url"].endswith("/campaigns/camp-123/send")

    @patch("routes.sender_routes.requests.request")
    def test_schedule_campaign_body(self, mock_request):
        mock_request.return_value = _response(200, {"scheduled": True})

        SenderRoutes.schedule_campaign("test-key", "camp-123", "2025-06-15 20:00:00")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "POST"
        assert kwargs["url"].endswith("/campaigns/camp-123/schedule")
        assert kwargs["json"] == {"schedule_time": "2025-06-15 20:00:00"}
        assert "scheduled_at" not in kwargs["json"]

    @patch("routes.sender_routes.requests.request")
    def test_get_campaign_stats_opens(self, mock_request):
        mock_request.return_value = _response(200, {"data": []})

        SenderRoutes.get_campaign_opens("test-key", "camp-123")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "GET"
        assert kwargs["url"].endswith("/campaigns/camp-123/opens")

    @patch("routes.sender_routes.requests.request")
    def test_get_campaign_stats_clicks(self, mock_request):
        mock_request.return_value = _response(200, {"data": []})

        SenderRoutes.get_campaign_clicks("test-key", "camp-123")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["url"].endswith("/campaigns/camp-123/clicks")

    @patch("routes.sender_routes.requests.request")
    def test_get_campaign_stats_hard_bounces(self, mock_request):
        mock_request.return_value = _response(200, {"data": []})

        SenderRoutes.get_campaign_bounces_hard("test-key", "camp-123")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["url"].endswith("/campaigns/camp-123/hard_bounces")

    @patch("routes.sender_routes.requests.request")
    def test_copy_campaign_url(self, mock_request):
        mock_request.return_value = _response(200, {"copied": True})

        SenderRoutes.copy_campaign("test-key", "camp-123")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "POST"
        assert kwargs["url"].endswith("/campaigns/camp-123/copy")

    @patch("routes.sender_routes.requests.request")
    def test_delete_campaign_query_param(self, mock_request):
        mock_request.return_value = _response(200, {"deleted": True})

        SenderRoutes.delete_campaign("test-key", "camp-123")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "DELETE"
        assert kwargs["url"].endswith("/campaigns")
        assert kwargs["params"] == {"ids": "[camp-123]"}


class TestGroupRoutes:
    """Unit tests for group subscriber routes."""

    @patch("routes.sender_routes.requests.request")
    def test_add_to_group_url(self, mock_request):
        mock_request.return_value = _response(200, {"ok": True})

        SenderRoutes.add_to_group("test-key", "x@test.com", "group-1")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "POST"
        assert kwargs["url"].endswith("/subscribers/groups/group-1")

    @patch("routes.sender_routes.requests.request")
    def test_remove_from_group_url(self, mock_request):
        mock_request.return_value = _response(200, {"ok": True})

        SenderRoutes.remove_from_group("test-key", "x@test.com", "group-1")

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "DELETE"
        assert kwargs["url"].endswith("/subscribers/groups/group-1")

    @patch("routes.sender_routes.requests.request")
    def test_list_group_subscribers(self, mock_request):
        mock_request.return_value = _response(200, {"data": []})

        SenderRoutes.list_group_subscribers("test-key", "group-1", params={"limit": 20})

        kwargs = mock_request.call_args.kwargs
        assert kwargs["method"] == "GET"
        assert kwargs["url"].endswith("/groups/group-1/subscribers")
        assert kwargs["params"] == {"limit": 20}
