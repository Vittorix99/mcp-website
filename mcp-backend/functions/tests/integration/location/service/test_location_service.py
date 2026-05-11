import pytest

from config.firebase_config import db
from dto.location_api import (
    GetEventLocationQueryDTO,
    ToggleLocationPublishedRequestDTO,
    UpdateEventLocationRequestDTO,
)
from dto.participant_api import SendLocationRequestDTO, SendLocationToAllRequestDTO
from errors.service_errors import NotFoundError


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
        SendLocationRequestDTO(
            eventId=event_id,
            participantId=participant_id,
            address="Via Roma 1",
            link="https://maps.example.com",
            message="A presto",
        )
    )
    assert result.message == "Location inviata con successo"

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

    location_snap = db.collection("event_locations").document(event_id).get()
    location_data = location_snap.to_dict() or {}
    assert location_data.get("address") == "Via Roma 1"
    assert location_data.get("maps_url") == "https://maps.example.com"


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
            SendLocationToAllRequestDTO(
                eventId=event_id,
                address="Via Roma 1",
                link="https://maps.example.com",
            )
        )
        assert result.status == "queued"
        job_id = result.job_id
        assert job_id
        job = job_repository.get_model(job_id)
        assert job is not None

        location_snap = db.collection("event_locations").document(event_id).get()
        location_data = location_snap.to_dict() or {}
        assert location_data.get("address") == "Via Roma 1"
        assert location_data.get("maps_url") == "https://maps.example.com"
    finally:
        if job_id:
            job_repository.collection.document(job_id).delete()


@pytest.mark.integration
def test_location_service_admin_update_publish_and_member_read(
    location_service,
    create_event,
):
    """Stores location details in event_locations and exposes them only when published."""
    event_id = create_event()

    admin_location = location_service.update_location(
        UpdateEventLocationRequestDTO(
            event_id=event_id,
            label="Secret Hall",
            maps_url="https://maps.example.com/public",
            maps_embed_url="https://maps.example.com/embed",
            address="Via Segreta 10",
            message="Usa il citofono MCP",
        )
    )
    assert admin_location.label == "Secret Hall"
    assert admin_location.maps_url == "https://maps.example.com/public"
    assert admin_location.maps_embed_url == "https://maps.example.com/embed"
    assert admin_location.address == "Via Segreta 10"
    assert admin_location.message == "Usa il citofono MCP"
    assert admin_location.published is False

    stored = db.collection("event_locations").document(event_id).get().to_dict() or {}
    assert stored == {
        "label": "Secret Hall",
        "maps_url": "https://maps.example.com/public",
        "maps_embed_url": "https://maps.example.com/embed",
        "address": "Via Segreta 10",
        "message": "Usa il citofono MCP",
    }

    with pytest.raises(NotFoundError):
        location_service.get_member_location(event_id)

    location_service.set_location_published(
        ToggleLocationPublishedRequestDTO(event_id=event_id, published=True)
    )

    admin_after_publish = location_service.get_admin_location(
        GetEventLocationQueryDTO(event_id=event_id)
    )
    assert admin_after_publish.published is True

    member_location = location_service.get_member_location(event_id)
    assert member_location.label == "Secret Hall"
    assert member_location.maps_url == "https://maps.example.com/public"
    assert member_location.maps_embed_url == "https://maps.example.com/embed"
    assert member_location.address == "Via Segreta 10"
    assert member_location.message == "Usa il citofono MCP"
    assert member_location.hint == "Ingresso principale"


@pytest.mark.integration
def test_location_service_missing_participant_fails(
    location_service,
    create_event,
):
    """Rejects missing participant id."""
    event_id = create_event()
    with pytest.raises(NotFoundError):
        location_service.send_location(
            SendLocationRequestDTO(
                eventId=event_id,
                participantId="missing-participant",
            )
        )
