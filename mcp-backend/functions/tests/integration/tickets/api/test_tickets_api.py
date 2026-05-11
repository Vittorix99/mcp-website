import pytest

from api.admin import participants_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_send_ticket_wrong_method_returns_405():
    """Non-POST requests are rejected with 405."""
    req = DummyRequest(method="GET", json={})
    resp, status = unwrap_response(participants_api.send_ticket(req))
    assert status == 405


@pytest.mark.integration
def test_send_ticket_missing_fields_returns_400():
    """Missing eventId/participantId returns 400."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(participants_api.send_ticket(req))
    assert status == 400


@pytest.mark.integration
def test_send_ticket_participant_not_found_returns_404(create_event):
    """Non-existent participantId returns 404."""
    event_id = create_event()
    req = DummyRequest(
        method="POST",
        json={"eventId": event_id, "participantId": "nonexistent-participant"},
    )
    resp, status = unwrap_response(participants_api.send_ticket(req))
    assert status == 404


@pytest.mark.integration
@pytest.mark.email
@pytest.mark.usefixtures("mailersend_api_key")
def test_send_ticket_sends_email_and_marks_participant(create_event, create_participant):
    """send_ticket endpoint generates PDF, sends email, and marks ticket_sent=True."""
    from config.firebase_config import db
    from services.events.documents_service import DocumentsService

    if DocumentsService().storage is None:
        pytest.skip("Storage bucket not configured for ticket generation")

    event_id = create_event()
    participant_id, _ = create_participant(event_id)

    req = DummyRequest(
        method="POST",
        json={"eventId": event_id, "participantId": participant_id},
    )
    resp, status = unwrap_response(participants_api.send_ticket(req))
    assert status == 200

    updated = (
        db.collection("participants")
        .document(event_id)
        .collection("participants_event")
        .document(participant_id)
        .get()
        .to_dict()
        or {}
    )
    assert updated.get("ticket_sent") is True
