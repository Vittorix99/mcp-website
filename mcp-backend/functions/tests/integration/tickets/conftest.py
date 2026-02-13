from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from dto import EventDTO
from models import EventParticipant, PaymentMethod
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from services.events_service import EventsService
from services.ticket_service import TicketService


@pytest.fixture
def ticket_service():
    return TicketService()


@pytest.fixture
def participant_repository():
    return ParticipantRepository()


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def create_event(events_service):
    created = []

    def _create():
        date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
        dto = EventDTO.from_payload(
            {
                "title": f"Integration Ticket {uuid4().hex[:8]}",
                "date": date_value,
                "startTime": "21:00",
                "endTime": "23:00",
                "location": "Integration Hall",
                "locationHint": "Ingresso principale",
                "price": 10.0,
                "fee": 1.0,
                "status": "active",
            }
        )
        result = events_service.create_event(dto, admin_uid="admin-test")
        event_id = result.get("eventId")
        created.append(event_id)
        return event_id

    yield _create

    for event_id in created:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")


@pytest.fixture
def create_participant(participant_repository, unique_email):
    created = []

    def _create(event_id: str):
        participant = EventParticipant(
            event_id=event_id,
            name="Mario",
            surname="Rossi",
            email=unique_email,
            phone="+390000000000",
            birthdate="01-01-1990",
            payment_method=PaymentMethod.WEBSITE,
        )
        participant_id = participant_repository.create_from_model(event_id, participant)
        created.append((event_id, participant_id))
        return participant_id, unique_email

    yield _create

    for event_id, participant_id in created:
        participant_repository.delete(event_id, participant_id)
