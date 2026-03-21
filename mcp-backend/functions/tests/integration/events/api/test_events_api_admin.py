import pytest

from api.admin import events_api as admin_events_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_admin_events_crud_api(base_event_payload):
    """Exercises admin events API CRUD endpoints end-to-end."""
    event_id = None
    try:
        create_req = DummyRequest(method="POST", json=base_event_payload)
        resp, status = unwrap_response(admin_events_api.admin_create_event(create_req))
        assert status == 201
        event_id = resp.get("eventId")
        assert event_id

        get_req = DummyRequest(method="GET", args={"id": event_id})
        resp, status = unwrap_response(admin_events_api.admin_get_event_by_id(get_req))
        assert status == 200
        assert resp.get("event", {}).get("id") == event_id

        update_req = DummyRequest(
            method="PUT",
            json={"id": event_id, "title": "Integration Updated"},
        )
        resp, status = unwrap_response(admin_events_api.admin_update_event(update_req))
        assert status == 200
        assert resp.get("eventId") == event_id

        list_req = DummyRequest(method="GET")
        resp, status = unwrap_response(admin_events_api.admin_get_all_events(list_req))
        assert status == 200
        assert any(item.get("id") == event_id for item in resp)
    finally:
        if event_id:
            delete_req = DummyRequest(method="DELETE", json={"id": event_id})
            unwrap_response(admin_events_api.admin_delete_event(delete_req))


@pytest.mark.integration
def test_admin_events_get_missing_id():
    """Returns 400 when admin event lookup is missing both id and slug."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(admin_events_api.admin_get_event_by_id(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_admin_events_create_invalid_date(base_event_payload):
    """Rejects invalid date formats on create."""
    payload = dict(base_event_payload)
    payload["date"] = "2026/99/99"
    req = DummyRequest(method="POST", json=payload)
    resp, status = unwrap_response(admin_events_api.admin_create_event(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_admin_events_update_invalid_numbers(base_event_payload):
    """Rejects invalid numeric fields on update."""
    event_id = None
    try:
        create_req = DummyRequest(method="POST", json=base_event_payload)
        resp, status = unwrap_response(admin_events_api.admin_create_event(create_req))
        assert status == 201
        event_id = resp.get("eventId")
        assert event_id

        update_req = DummyRequest(
            method="PUT",
            json={"id": event_id, "price": "not-a-number", "maxParticipants": "oops"},
        )
        resp, status = unwrap_response(admin_events_api.admin_update_event(update_req))
        assert status == 400
        assert resp.get("error")
    finally:
        if event_id:
            delete_req = DummyRequest(method="DELETE", json={"id": event_id})
            unwrap_response(admin_events_api.admin_delete_event(delete_req))
