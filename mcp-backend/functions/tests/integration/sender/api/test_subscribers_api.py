from unittest.mock import patch

import pytest

from api.admin.sender import subscribers_api
from tests.utils import DummyRequest, unwrap_response


pytestmark = pytest.mark.integration


@patch("routes.sender_routes.requests.request")
def test_subscribers_upsert_integration(mock_request, sender_response_factory):
    """POST subscribers forwards upsert data through service/routes."""
    mock_request.return_value = sender_response_factory(200, {"data": {"id": "sub-1", "email": "x@test.com"}})

    req = DummyRequest(
        method="POST",
        json={
            "email": "x@test.com",
            "firstname": "Mario",
            "lastname": "Rossi",
            "groups": ["g1"],
            "fields": {"membership_id": "M-1"},
        },
    )
    resp, status = unwrap_response(subscribers_api.admin_sender_subscribers(req))

    assert status == 200
    assert resp["data"]["id"] == "sub-1"
    assert mock_request.call_args.kwargs["method"] == "POST"
    assert mock_request.call_args.kwargs["url"].endswith("/subscribers")
    assert mock_request.call_args.kwargs["json"]["email"] == "x@test.com"


@patch("routes.sender_routes.requests.request")
def test_subscribers_update_integration(mock_request, sender_response_factory):
    """PUT subscribers maps to PATCH /subscribers/{email} without email in body."""
    mock_request.return_value = sender_response_factory(200, {"data": {"updated": True}})

    req = DummyRequest(method="PUT", json={"email": "x@test.com", "firstname": "Luigi"})
    resp, status = unwrap_response(subscribers_api.admin_sender_subscribers(req))

    assert status == 200
    assert resp == {"data": {"updated": True}}
    assert mock_request.call_args.kwargs["method"] == "PATCH"
    assert mock_request.call_args.kwargs["url"].endswith("/subscribers/x@test.com")
    assert mock_request.call_args.kwargs["json"] == {"firstname": "Luigi"}


@patch("routes.sender_routes.requests.request")
def test_subscribers_delete_integration(mock_request, sender_response_factory):
    """DELETE subscribers calls Sender batch-delete route and returns deleted=true."""
    mock_request.return_value = sender_response_factory(200, {"deleted": True})

    req = DummyRequest(method="DELETE", json={"email": "x@test.com"})
    resp, status = unwrap_response(subscribers_api.admin_sender_subscribers(req))

    assert status == 200
    assert resp == {"deleted": True}
    assert mock_request.call_args.kwargs["method"] == "DELETE"
    assert mock_request.call_args.kwargs["url"].endswith("/subscribers")
    assert mock_request.call_args.kwargs["json"] == {"subscribers": ["x@test.com"]}


@patch("routes.sender_routes.requests.request")
def test_subscriber_groups_add_remove_integration(mock_request, sender_response_factory):
    """Group assignment endpoints call Sender add/remove group routes."""
    mock_request.side_effect = [
        sender_response_factory(200, {"success": True}),
        sender_response_factory(200, {"success": True}),
    ]

    add_req = DummyRequest(method="POST", json={"email": "x@test.com", "group_id": "g-1"})
    add_resp, add_status = unwrap_response(subscribers_api.admin_sender_subscriber_groups(add_req))
    assert add_status == 200
    assert add_resp == {"added": True}

    remove_req = DummyRequest(method="DELETE", json={"email": "x@test.com", "group_id": "g-1"})
    remove_resp, remove_status = unwrap_response(subscribers_api.admin_sender_subscriber_groups(remove_req))
    assert remove_status == 200
    assert remove_resp == {"removed": True}

    first = mock_request.call_args_list[0].kwargs
    second = mock_request.call_args_list[1].kwargs
    assert first["url"].endswith("/subscribers/groups/g-1")
    assert second["url"].endswith("/subscribers/groups/g-1")
    assert first["method"] == "POST"
    assert second["method"] == "DELETE"


@patch("routes.sender_routes.requests.request")
def test_subscriber_events_integration(mock_request, sender_response_factory):
    """GET subscriber events forwards identifier and actions query."""
    mock_request.return_value = sender_response_factory(200, {"data": [{"action": "open"}]})

    req = DummyRequest(method="GET", args={"email": "x@test.com", "actions": "open"})
    resp, status = unwrap_response(subscribers_api.admin_sender_subscriber_events(req))

    assert status == 200
    assert resp == {"data": [{"action": "open"}]}
    assert mock_request.call_args.kwargs["method"] == "GET"
    assert mock_request.call_args.kwargs["url"].endswith("/subscribers/x@test.com/events")
    assert mock_request.call_args.kwargs["params"] == {"actions": "open"}
