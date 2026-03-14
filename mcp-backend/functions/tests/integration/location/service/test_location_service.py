import pytest

from config.firebase_config import db
from errors.service_errors import ValidationError


@pytest.mark.integration
@pytest.mark.email
@pytest.mark.usefixtures("mailersend_api_key")
def test_location_service_send_location_updates_firestore_and_sends_email(
    location_service,
    create_event,
    create_participant,
):
    """Sends location email and updates participant location_sent fields."""
    event_id = create_event()
    participant_id, _participant_email = create_participant(event_id)

    result = location_service.send_location(
        event_id,
        participant_id,
        address="Via Roma 1",
        link="https://maps.example.com",
        message="A presto",
    )
    assert result.get("message") == "Location inviata con successo"

    snap = (
        db.collection("participants")
        .document(event_id)
        .collection("participants_event")
        .document(participant_id)
        .get()
    )
    data = snap.to_dict() or {}
    assert data.get("location_sent") is True
    assert data.get("location_sent_at") is not None


@pytest.mark.integration
def test_location_service_start_job_creates_job_record(
    location_service,
    create_event,
    job_repository,
):
    """Creates a queued job for bulk location sending."""
    event_id = create_event()
    job_id = None
    try:
        result = location_service.start_send_location_job(
            event_id,
            address="Via Roma 1",
            link="https://maps.example.com",
        )
        assert result.get("status") == "queued"
        job_id = result.get("jobId")
        assert job_id
        job = job_repository.get(job_id)
        assert job is not None
    finally:
        if job_id:
            job_repository.collection.document(job_id).delete()


@pytest.mark.integration
def test_location_service_missing_participant_fails(
    location_service,
    create_event,
):
    """Rejects missing participant id."""
    event_id = create_event()
    with pytest.raises(ValidationError):
        location_service.send_location(event_id, None)
