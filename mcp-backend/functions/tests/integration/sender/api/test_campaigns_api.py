from unittest.mock import patch

import pytest

from api.admin.sender import campaigns_api
from tests.utils import DummyRequest, unwrap_response


pytestmark = pytest.mark.integration


@patch("clients.sender_client.requests.request")
def test_campaigns_get_list_integration(mock_request, sender_response_factory):
    """GET campaigns returns Sender payload through API->service->routes chain."""
    mock_request.return_value = sender_response_factory(200, {"data": [{"id": "camp-1"}]})

    req = DummyRequest(method="GET", args={"status": "draft"})
    resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

    assert status == 200
    assert resp == {"data": [{"id": "camp-1"}]}
    assert mock_request.call_args.kwargs["method"] == "GET"
    assert mock_request.call_args.kwargs["url"].endswith("/campaigns")
    assert mock_request.call_args.kwargs["params"] == {"status": "draft"}


@patch("clients.sender_client.requests.request")
def test_campaigns_create_maps_body_integration(mock_request, sender_response_factory):
    """POST create campaign maps frontend fields to Sender body format."""
    mock_request.return_value = sender_response_factory(201, {"data": {"id": "camp-2"}})

    req = DummyRequest(
        method="POST",
        json={
            "title": "Evento",
            "subject": "Annuncio",
            "from_name": "MCP",
            "from_email": "info@test.com",
            "reply_to": "reply@test.com",
            "content_html": "<p>Hello</p>",
            "groups": ["g-news"],
        },
    )
    resp, status = unwrap_response(campaigns_api.admin_sender_campaigns(req))

    assert status == 200
    assert resp == {"data": {"id": "camp-2"}}
    sent_json = mock_request.call_args.kwargs["json"]
    assert sent_json == {
        "title": "Evento",
        "subject": "Annuncio",
        "from": "MCP",
        "reply_to": "reply@test.com",
        "content_type": "html",
        "content": "<p>Hello</p>",
        "groups": ["g-news"],
    }


@patch("clients.sender_client.requests.request")
def test_campaign_send_422_returns_error_payload(mock_request, sender_response_factory):
    """Send endpoint surfaces Sender validation errors as 422."""
    payload = {"error": [{"title": "Unsubscribe link", "details": "missing"}]}
    mock_request.return_value = sender_response_factory(422, payload)

    req = DummyRequest(method="POST", json={"id": "camp-3"})
    resp, status = unwrap_response(campaigns_api.admin_sender_campaign_send(req))

    assert status == 422
    assert resp["sent"] is False
    assert "Unsubscribe link" in resp["error"]
    assert mock_request.call_args.kwargs["url"].endswith("/campaigns/camp-3/send")


@patch("clients.sender_client.requests.request")
def test_campaign_schedule_converts_iso_to_sender_format(mock_request, sender_response_factory):
    """Schedule endpoint converts ISO datetime to Sender UTC format."""
    mock_request.return_value = sender_response_factory(200, {"scheduled": True})

    req = DummyRequest(
        method="POST",
        json={"id": "camp-4", "scheduled_at": "2025-06-15T22:00:00+02:00"},
    )
    resp, status = unwrap_response(campaigns_api.admin_sender_campaign_schedule(req))

    assert status == 200
    assert resp == {"scheduled": True}
    assert mock_request.call_args.kwargs["url"].endswith("/campaigns/camp-4/schedule")
    assert mock_request.call_args.kwargs["json"] == {"schedule_time": "2025-06-15 20:00:00"}


@patch("clients.sender_client.requests.request")
def test_campaign_stats_clicks_routes_to_clicks_endpoint(mock_request, sender_response_factory):
    """Stats endpoint delegates to /campaigns/{id}/clicks."""
    mock_request.return_value = sender_response_factory(200, {"data": [{"email": "x@test.com"}]})

    req = DummyRequest(method="GET", args={"id": "camp-5", "type": "clicks"})
    resp, status = unwrap_response(campaigns_api.admin_sender_campaign_stats(req))

    assert status == 200
    assert resp == {"data": [{"email": "x@test.com"}]}
    assert mock_request.call_args.kwargs["url"].endswith("/campaigns/camp-5/clicks")


@patch("clients.sender_client.requests.request")
def test_campaign_copy_endpoint_integration(mock_request, sender_response_factory):
    """Copy endpoint calls Sender /campaigns/{id}/copy route."""
    mock_request.return_value = sender_response_factory(200, {"data": {"id": "camp-copy"}})

    req = DummyRequest(method="POST", json={"id": "camp-6"})
    resp, status = unwrap_response(campaigns_api.admin_sender_campaign_copy(req))

    assert status == 200
    assert resp == {"data": {"id": "camp-copy"}}
    assert mock_request.call_args.kwargs["url"].endswith("/campaigns/camp-6/copy")
