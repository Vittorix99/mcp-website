from unittest.mock import patch

import pytest

from api.admin.sender import groups_api
from tests.utils import DummyRequest, unwrap_response


pytestmark = pytest.mark.integration


@patch("clients.sender_client.requests.request")
def test_groups_list_create_rename_delete_integration(mock_request, sender_response_factory):
    """Groups API supports list/create/rename/delete through Sender routes."""
    mock_request.side_effect = [
        sender_response_factory(200, {"data": [{"id": "g1", "title": "Newsletter"}]}),
        sender_response_factory(200, {"data": {"id": "g2", "title": "Events"}}),
        sender_response_factory(200, {"data": {"id": "g2", "title": "Events VIP"}}),
        sender_response_factory(200, {"deleted": True}),
    ]

    list_resp, list_status = unwrap_response(groups_api.admin_sender_groups(DummyRequest(method="GET")))
    assert list_status == 200
    assert list_resp["data"][0]["id"] == "g1"

    create_resp, create_status = unwrap_response(
        groups_api.admin_sender_groups(DummyRequest(method="POST", json={"name": "Events"}))
    )
    assert create_status == 200
    assert create_resp["data"]["id"] == "g2"

    rename_resp, rename_status = unwrap_response(
        groups_api.admin_sender_groups(DummyRequest(method="PUT", json={"id": "g2", "title": "Events VIP"}))
    )
    assert rename_status == 200
    assert rename_resp["data"]["title"] == "Events VIP"

    delete_resp, delete_status = unwrap_response(
        groups_api.admin_sender_groups(DummyRequest(method="DELETE", json={"id": "g2"}))
    )
    assert delete_status == 200
    assert delete_resp == {"deleted": True}

    calls = mock_request.call_args_list
    assert calls[0].kwargs["url"].endswith("/groups")
    assert calls[1].kwargs["json"] == {"title": "Events"}
    assert calls[2].kwargs["url"].endswith("/groups/g2")
    assert calls[2].kwargs["method"] == "PATCH"
    assert calls[3].kwargs["url"].endswith("/groups/g2")
    assert calls[3].kwargs["method"] == "DELETE"


@patch("clients.sender_client.requests.request")
def test_group_subscribers_integration(mock_request, sender_response_factory):
    """Group subscribers endpoint calls /groups/{group_id}/subscribers with passthrough params."""
    mock_request.return_value = sender_response_factory(200, {"data": [{"email": "x@test.com"}]})

    req = DummyRequest(method="GET", args={"id": "g-9", "page": "2"})
    resp, status = unwrap_response(groups_api.admin_sender_group_subscribers(req))

    assert status == 200
    assert resp == {"data": [{"email": "x@test.com"}]}
    assert mock_request.call_args.kwargs["url"].endswith("/groups/g-9/subscribers")
    assert mock_request.call_args.kwargs["params"] == {"page": "2"}
