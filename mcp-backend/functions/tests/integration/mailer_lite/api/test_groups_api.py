import pytest

from api.admin.mailer_lite import groups_api, subscribers_api
from tests.utils import DummyRequest, unwrap_response


def _extract_id(payload):
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and "id" in data:
            return data["id"]
        if "id" in payload:
            return payload["id"]
    return None


@pytest.mark.integration
def test_groups_crud_api(unique_group_name):
    """Verify groups CRUD endpoints return expected data via the API."""
    create_req = DummyRequest(method="POST", json={"name": unique_group_name})
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(create_req))
    assert status == 200
    group_id = _extract_id(resp)
    assert group_id is not None

    list_req = DummyRequest(method="GET", args={"filter": f'{{"name": "{unique_group_name}"}}'})
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(list_req))
    assert status == 200
    data = resp.get("data", []) if isinstance(resp, dict) else []
    assert any(str(item.get("id")) == str(group_id) for item in data)

    delete_req = DummyRequest(method="DELETE", json={"id": group_id})
    resp, status = unwrap_response(groups_api.admin_mailerlite_groups(delete_req))
    assert status == 200


@pytest.mark.integration
def test_group_assign_unassign_api(unique_group_name, unique_email):
    """Verify assign/unassign subscriber to group through the API."""
    group_id = None
    subscriber_id = None
    try:
        create_group = DummyRequest(method="POST", json={"name": unique_group_name})
        group_resp, status = unwrap_response(groups_api.admin_mailerlite_groups(create_group))
        assert status == 200
        group_id = _extract_id(group_resp)
        assert group_id is not None

        create_sub = DummyRequest(
            method="POST",
            json={"email": unique_email, "fields": {"birthdate": "01-01-1999", "phone": "+390000000000"}},
        )
        sub_resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(create_sub))
        assert status == 200
        subscriber_id = _extract_id(sub_resp)
        assert subscriber_id is not None

        assign_req = DummyRequest(method="POST", json={"group_id": group_id, "subscriber_id": subscriber_id})
        resp, status = unwrap_response(groups_api.admin_mailerlite_group_assign_subscriber(assign_req))
        assert status == 200

        list_req = DummyRequest(method="GET", args={"group_id": group_id})
        resp, status = unwrap_response(groups_api.admin_mailerlite_group_subscribers(list_req))
        assert status == 200

        unassign_req = DummyRequest(method="DELETE", json={"group_id": group_id, "subscriber_id": subscriber_id})
        resp, status = unwrap_response(groups_api.admin_mailerlite_group_unassign_subscriber(unassign_req))
        assert status == 200
    finally:
        if subscriber_id is not None:
            delete_sub = DummyRequest(method="DELETE", json={"id": subscriber_id})
            unwrap_response(subscribers_api.admin_mailerlite_subscribers(delete_sub))
        if group_id is not None:
            delete_group = DummyRequest(method="DELETE", json={"id": group_id})
            unwrap_response(groups_api.admin_mailerlite_groups(delete_group))
