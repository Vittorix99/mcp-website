import pytest

from api.public import events_tickets_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_public_check_participants_duplicate_detected(
    create_event,
    participants_service,
    participant_payload,
):
    """Public API returns validation_error when duplicates are detected."""
    event_id = create_event()
    payload = dict(participant_payload, event_id=event_id)
    participant_id = None
    try:
        result = participants_service.create(payload)
        participant_id = result.get("id")
        assert participant_id

        req = DummyRequest(
            method="POST",
            json={"eventId": event_id, "participants": [participant_payload]},
        )
        resp, status = unwrap_response(events_tickets_api.check_participants(req))
        assert status == 400
        assert resp.get("error") == "validation_error"
        messages = resp.get("messages") or []
        assert any("già acquistato" in msg or "duplicati" in msg for msg in messages)
    finally:
        if participant_id:
            participants_service.delete(event_id, participant_id)

