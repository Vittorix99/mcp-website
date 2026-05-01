import pytest

from api.public import events_api as public_events_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_public_events_api_endpoints(events_service, event_dto):
    """Exercises public events API endpoints on a real Firestore emulator."""
    event_id = None
    try:
        created = events_service.create_event(event_dto, admin_uid="admin-test")
        event_id = created.event_id
        assert event_id

        list_req = DummyRequest(method="GET")
        resp, status = unwrap_response(public_events_api.get_all_events(list_req))
        assert status == 200
        matched = [item for item in resp if item.get("id") == event_id]
        assert matched
        assert "location" not in matched[0]

        get_req = DummyRequest(method="GET", args={"id": event_id})
        resp, status = unwrap_response(public_events_api.get_event_by_id(get_req))
        assert status == 200
        assert resp.get("id") == event_id
        assert "location" not in resp

        next_req = DummyRequest(method="GET")
        resp, status = unwrap_response(public_events_api.get_next_event(next_req))
        assert status == 200
        assert any(item.get("id") == event_id for item in resp)
    finally:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")


@pytest.mark.integration
def test_public_events_get_missing_id():
    """Returns 400 when public event lookup is missing both id and slug."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(public_events_api.get_event_by_id(req))
    assert status == 400
    assert resp.get("error")
