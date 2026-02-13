import pytest

from dto import EventDTO
from models import EventPurchaseAccessType


@pytest.mark.integration
def test_events_service_crud(events_service, event_repository, event_dto):
    """Creates, updates, and deletes an event via the service layer."""
    event_id = None
    try:
        created = events_service.create_event(event_dto, admin_uid="admin-test")
        event_id = created.get("eventId")
        assert event_id

        stored = event_repository.get_model(event_id)
        assert stored is not None
        assert stored.title == event_dto.title

        update_dto = EventDTO.from_payload({"title": "Updated Title", "price": 15.0})
        updated = events_service.update_event(event_id, update_dto, admin_uid="admin-test")
        assert updated.get("eventId") == event_id

        refreshed = event_repository.get_model(event_id)
        assert refreshed is not None
        assert refreshed.title == "Updated Title"
        assert refreshed.price == 15.0
    finally:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")


@pytest.mark.integration
def test_events_service_get_by_id_and_slug(events_service, event_repository, event_dto):
    """Fetches an event by id and slug from the service layer."""
    event_id = None
    try:
        created = events_service.create_event(event_dto, admin_uid="admin-test")
        event_id = created.get("eventId")
        assert event_id

        payload = events_service.get_event_by_id(event_id=event_id)
        assert payload.get("event", {}).get("id") == event_id

        model = event_repository.get_model(event_id)
        assert model is not None
        payload_by_slug = events_service.get_event_by_id(slug=model.slug)
        assert payload_by_slug.get("event", {}).get("id") == event_id
    finally:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")


@pytest.mark.integration
def test_events_service_public_list_and_next(events_service, event_dto):
    """Lists public events and upcoming events using the service layer."""
    event_id = None
    try:
        created = events_service.create_event(event_dto, admin_uid="admin-test")
        event_id = created.get("eventId")
        assert event_id

        public_events = events_service.list_public_events(view="card")
        assert any(item.get("id") == event_id for item in public_events)

        next_events = events_service.get_next_public_event()
        assert any(item.get("id") == event_id for item in next_events)
    finally:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")


@pytest.mark.integration
def test_events_service_purchase_mode_and_flags(events_service, event_repository, base_event_payload):
    """Persists purchase_mode and constraint flags on create."""
    event_id = None
    try:
        payload = dict(base_event_payload)
        payload.update(
            {
                "purchaseMode": "ONLY_MEMBERS",
                "allowDuplicates": True,
                "over21Only": True,
                "onlyFemales": True,
                "maxParticipants": 80,
            }
        )
        dto = EventDTO.from_payload(payload)
        created = events_service.create_event(dto, admin_uid="admin-test")
        event_id = created.get("eventId")
        assert event_id

        stored = event_repository.get_model(event_id)
        assert stored is not None
        assert stored.purchase_mode == EventPurchaseAccessType.ONLY_MEMBERS
        assert stored.allow_duplicates is True
        assert stored.over21_only is True
        assert stored.only_females is True
        assert stored.max_participants == 80
    finally:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")
