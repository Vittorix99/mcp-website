import pytest

from config.firebase_config import db


@pytest.mark.integration
@pytest.mark.email
@pytest.mark.usefixtures("mailersend_api_key")
def test_ticket_service_sends_email_and_updates_participant(
    ticket_service,
    create_event,
    create_participant,
):
    """Generates a ticket, sends email, and updates participant document."""
    if ticket_service.documents_service.storage is None:
        pytest.skip("Storage bucket not configured for ticket generation")

    event_id = create_event()
    participant_id, _participant_email = create_participant(event_id)

    participant_snap = (
        db.collection("participants")
        .document(event_id)
        .collection("participants_event")
        .document(participant_id)
        .get()
    )
    participant_data = participant_snap.to_dict() or {}
    participant_data["event_id"] = event_id

    result = ticket_service.process_new_ticket(participant_id, participant_data, send=True)
    assert result.get("success") is True

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
    assert updated.get("ticket_pdf_url")

    event_payload = db.collection("events").document(event_id).get().to_dict() or {}
    storage_path = ticket_service._build_storage_path(
        event_payload.get("title"),
        participant_data.get("name"),
        participant_data.get("surname"),
    )
    blob = ticket_service.documents_service.storage.blob(storage_path)
    if blob.exists():
        blob.delete()
