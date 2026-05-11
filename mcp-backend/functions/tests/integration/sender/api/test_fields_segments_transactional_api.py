from unittest.mock import patch

import pytest

from api.admin.sender import fields_api, segments_api, transactional_api
from tests.utils import DummyRequest, unwrap_response


pytestmark = pytest.mark.integration


@patch("clients.sender_client.requests.request")
def test_fields_list_create_delete_integration(mock_request, sender_response_factory):
    """Fields API integration: list/create/delete via Sender endpoints."""
    mock_request.side_effect = [
        sender_response_factory(200, {"data": [{"id": "f1", "title": "membership_id"}]}),
        sender_response_factory(200, {"data": {"id": "f2", "title": "event_id"}}),
        sender_response_factory(200, {"deleted": True}),
    ]

    list_resp, list_status = unwrap_response(fields_api.admin_sender_fields(DummyRequest(method="GET")))
    assert list_status == 200
    assert list_resp["data"][0]["id"] == "f1"

    create_resp, create_status = unwrap_response(
        fields_api.admin_sender_fields(DummyRequest(method="POST", json={"title": "event_id", "type": "string"}))
    )
    assert create_status == 200
    assert create_resp["data"]["id"] == "f2"

    delete_resp, delete_status = unwrap_response(
        fields_api.admin_sender_fields(DummyRequest(method="DELETE", json={"id": "f2"}))
    )
    assert delete_status == 200
    assert delete_resp == {"deleted": True}

    calls = mock_request.call_args_list
    assert calls[0].kwargs["url"].endswith("/fields")
    assert calls[1].kwargs["json"] == {"title": "event_id", "type": "string"}
    assert calls[2].kwargs["url"].endswith("/fields/f2")
    assert calls[2].kwargs["method"] == "DELETE"


@patch("clients.sender_client.requests.request")
def test_segments_get_delete_and_subscribers_integration(mock_request, sender_response_factory):
    """Segments API integration for get single, list subscribers, and delete."""
    mock_request.side_effect = [
        sender_response_factory(200, {"data": {"id": "s1", "title": "VIP"}}),
        sender_response_factory(200, {"data": [{"email": "x@test.com"}]}),
        sender_response_factory(200, {"deleted": True}),
    ]

    get_resp, get_status = unwrap_response(segments_api.admin_sender_segments(DummyRequest(method="GET", args={"id": "s1"})))
    assert get_status == 200
    assert get_resp["data"]["id"] == "s1"

    subs_resp, subs_status = unwrap_response(
        segments_api.admin_sender_segment_subscribers(DummyRequest(method="GET", args={"segment_id": "s1"}))
    )
    assert subs_status == 200
    assert subs_resp["data"][0]["email"] == "x@test.com"

    del_resp, del_status = unwrap_response(segments_api.admin_sender_segments(DummyRequest(method="DELETE", args={"id": "s1"})))
    assert del_status == 200
    assert del_resp == {"deleted": True}

    calls = mock_request.call_args_list
    assert calls[0].kwargs["url"].endswith("/segments/s1")
    assert calls[1].kwargs["url"].endswith("/segments/s1/subscribers")
    assert calls[2].kwargs["url"].endswith("/segments/s1")
    assert calls[2].kwargs["method"] == "DELETE"


@patch("clients.sender_client.requests.request")
def test_transactional_list_create_send_integration(mock_request, sender_response_factory):
    """Transactional APIs list/create/send with expected Sender routes and bodies."""
    mock_request.side_effect = [
        sender_response_factory(200, {"data": [{"id": "tc-1"}]}),
        sender_response_factory(200, {"data": {"id": "tc-2"}}),
        sender_response_factory(200, {"sent": True}),
    ]

    list_resp, list_status = unwrap_response(transactional_api.admin_sender_transactional(DummyRequest(method="GET")))
    assert list_status == 200
    assert list_resp["data"][0]["id"] == "tc-1"

    create_resp, create_status = unwrap_response(
        transactional_api.admin_sender_transactional(
            DummyRequest(
                method="POST",
                json={
                    "title": "Event Followup",
                    "subject": "Lineup out now",
                    "from_name": "MCP",
                    "from_email": "info@test.com",
                    "content_html": "<p>Lineup</p>",
                },
            )
        )
    )
    assert create_status == 200
    assert create_resp["data"]["id"] == "tc-2"

    send_resp, send_status = unwrap_response(
        transactional_api.admin_sender_transactional_send(
            DummyRequest(
                method="POST",
                json={
                    "campaign_id": "tc-2",
                    "to_email": "x@test.com",
                    "to_name": "Mario",
                    "variables": {"event_title": "EP12"},
                },
            )
        )
    )
    assert send_status == 200
    assert send_resp == {"sent": True}

    calls = mock_request.call_args_list
    assert calls[0].kwargs["url"].endswith("/transactional-campaigns")
    assert calls[1].kwargs["json"] == {
        "title": "Event Followup",
        "subject": "Lineup out now",
        "from": {"name": "MCP", "email": "info@test.com"},
        "content": {"html": "<p>Lineup</p>"},
    }
    assert calls[2].kwargs["url"].endswith("/transactional-campaigns/tc-2/send")
    assert calls[2].kwargs["json"] == {
        "to": [{"email": "x@test.com", "name": "Mario"}],
        "variables": {"event_title": "EP12"},
    }


def test_transactional_delete_not_supported():
    """DELETE transactional campaigns is not an allowed endpoint method."""
    req = DummyRequest(method="DELETE", json={"id": "tc-2"})
    resp, status = unwrap_response(transactional_api.admin_sender_transactional(req))

    assert status == 405
    assert resp == {"error": "Invalid method"}
