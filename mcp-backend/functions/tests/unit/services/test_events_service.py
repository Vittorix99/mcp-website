import datetime

import pytest
from firebase_admin import firestore

from dto import EventDTO
from models import Event
from services.events_service import EventsService
from services.service_errors import NotFoundError, ValidationError


class _DummyEventRepo:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.models = {}
        self.by_slug = {}
        self._stream = []

    def create_from_model(self, event, slug_seed):
        event_id = "event-1"
        self.created.append((event, slug_seed))
        self.models[event_id] = event
        return event_id

    def get_model(self, event_id):
        return self.models.get(event_id)

    def get_model_by_slug(self, slug):
        return self.by_slug.get(slug)

    def update_from_model(self, event_id, event):
        self.updated.append((event_id, event))
        self.models[event_id] = event

    def delete(self, event_id):
        self.deleted.append(event_id)
        self.models.pop(event_id, None)

    def stream_models(self):
        for event in self._stream:
            yield event


class _DummyParticipantRepo:
    def __init__(self, counts=None):
        self.counts = counts or {}

    def count(self, event_id):
        return self.counts.get(event_id, 0)


def _make_service():
    service = EventsService()
    service.event_repository = _DummyEventRepo()
    service.participant_repository = _DummyParticipantRepo()
    return service


def test_create_event_happy_path():
    service = _make_service()
    dto = EventDTO(
        title="Test Event",
        date="13-02-2026",
        start_time="20:00",
        location="Milano",
        location_hint="Ingresso A",
        price=10,
        fee=1,
    )

    payload = service.create_event(dto, admin_uid="admin-1")

    assert payload["eventId"] == "event-1"
    created_event, slug_seed = service.event_repository.created[0]
    assert created_event.title == "Test Event"
    assert created_event.date == "13-02-2026"
    assert created_event.participants_count == 0
    assert created_event.created_by == "admin-1"
    assert slug_seed == "Test Event 13-02-2026"


def test_create_event_rejects_invalid_date():
    service = _make_service()
    dto = EventDTO(
        title="Test",
        date="2026-99-99",
        start_time="20:00",
        location="Milano",
        location_hint="Ingresso A",
    )
    with pytest.raises(ValidationError):
        service.create_event(dto, admin_uid="admin-1")


def test_update_event_not_found():
    service = _make_service()
    dto = EventDTO(title="Updated")
    with pytest.raises(NotFoundError):
        service.update_event("missing", dto, admin_uid="admin-1")


def test_update_event_rejects_invalid_max_participants():
    service = _make_service()
    event = Event(title="Old", date="13-02-2026")
    service.event_repository.models["evt"] = event

    dto = EventDTO(max_participants="abc")
    dto.fields_present = {"maxParticipants"}
    with pytest.raises(ValidationError):
        service.update_event("evt", dto, admin_uid="admin-1")


def test_update_event_happy_path():
    service = _make_service()
    event = Event(title="Old", date="13-02-2026")
    service.event_repository.models["evt"] = event

    dto = EventDTO(title="New", price="12.5")
    dto.fields_present = {"title", "price"}
    payload = service.update_event("evt", dto, admin_uid="admin-1")

    assert payload["eventId"] == "evt"
    updated_event = service.event_repository.models["evt"]
    assert updated_event.title == "New"
    assert updated_event.price == 12.5
    assert updated_event.updated_by == "admin-1"
    assert updated_event.updated_at == firestore.SERVER_TIMESTAMP


def test_delete_event_happy_path():
    service = _make_service()
    event = Event(title="Old", date="13-02-2026")
    service.event_repository.models["evt"] = event

    payload = service.delete_event("evt", admin_uid="admin-1")

    assert payload["eventId"] == "evt"
    assert "evt" in service.event_repository.deleted


def test_get_all_events_sets_participants_count():
    service = _make_service()
    event1 = Event(title="A", date="13-02-2026")
    event1.id = "evt-1"
    event2 = Event(title="B", date="14-02-2026")
    event2.id = "evt-2"
    service.event_repository._stream = [event1, event2]
    service.participant_repository = _DummyParticipantRepo(counts={"evt-1": 3, "evt-2": 1})

    payload = service.get_all_events()

    assert len(payload) == 2
    assert payload[0]["participantsCount"] == 3
    assert payload[1]["participantsCount"] == 1


def test_get_event_by_id_uses_slug():
    service = _make_service()
    event = Event(title="Slugged", date="13-02-2026")
    service.event_repository.by_slug["slug-1"] = event

    payload = service.get_event_by_id(slug="slug-1")

    assert payload["event"]["title"] == "Slugged"


def test_list_public_events_respects_view():
    service = _make_service()
    event = Event(title="Public", date="13-02-2026")
    event.id = "evt-1"
    event.slug = "evt-1"
    service.event_repository._stream = [event]

    payload = service.list_public_events(view="ids")

    assert payload == [{"id": "evt-1", "slug": "evt-1"}]


def test_list_upcoming_events_filters_and_sorts():
    service = _make_service()
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    event_today = Event(title="Today", date=today.strftime("%d-%m-%Y"))
    event_today.id = "evt-today"
    event_tomorrow = Event(title="Tomorrow", date=tomorrow.strftime("%d-%m-%Y"))
    event_tomorrow.id = "evt-tomorrow"
    event_yesterday = Event(title="Yesterday", date=yesterday.strftime("%d-%m-%Y"))
    event_yesterday.id = "evt-yesterday"

    service.event_repository._stream = [event_tomorrow, event_yesterday, event_today]

    payload = service.list_upcoming_events(limit=1)

    assert payload[0]["title"] == "Today"
    assert len(payload) == 1


def test_get_next_public_event_returns_future_events():
    service = _make_service()
    today = datetime.datetime.now().date()
    tomorrow = today + datetime.timedelta(days=1)

    event_today = Event(title="Today", date=today.strftime("%d-%m-%Y"))
    event_tomorrow = Event(title="Tomorrow", date=tomorrow.strftime("%d-%m-%Y"))

    service.event_repository._stream = [event_tomorrow, event_today]

    payload = service.get_next_public_event()

    assert [event["title"] for event in payload] == ["Today", "Tomorrow"]
