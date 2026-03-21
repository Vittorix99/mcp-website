import pytest

from api.admin import participants_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_participants_admin_api_crud(create_event, participant_payload):
    """CRUD flow through admin participants endpoints."""
    event_id = create_event()
    participant_id = None
    try:
        create_req = DummyRequest(
            method="POST",
            json={**participant_payload, "event_id": event_id},
        )
        resp, status = unwrap_response(participants_api.create_participant(create_req))
        assert status == 201
        participant_id = resp.get("id")
        assert participant_id

        list_req = DummyRequest(method="POST", json={"eventId": event_id})
        resp, status = unwrap_response(participants_api.get_participants_by_event(list_req))
        assert status == 200
        assert any(item.get("id") == participant_id for item in resp)

        get_req = DummyRequest(
            method="POST",
            json={"eventId": event_id, "participantId": participant_id},
        )
        resp, status = unwrap_response(participants_api.get_participant(get_req))
        assert status == 200
        assert resp.get("id") == participant_id

        update_req = DummyRequest(
            method="PUT",
            json={"event_id": event_id, "participantId": participant_id, "phone": "+390000000999"},
        )
        resp, status = unwrap_response(participants_api.update_participant(update_req))
        assert status == 200
    finally:
        if participant_id:
            delete_req = DummyRequest(
                method="DELETE",
                json={"event_id": event_id, "participantId": participant_id},
            )
            unwrap_response(participants_api.delete_participant(delete_req))


@pytest.mark.integration
def test_participants_admin_api_missing_event_id():
    """Returns 400 when eventId is missing."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(participants_api.get_participants_by_event(req))
    assert status == 400
    assert resp.get("error")
