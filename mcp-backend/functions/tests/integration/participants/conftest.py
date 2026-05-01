from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from dto.event_api import CreateEventRequestDTO
from models import EventPurchaseAccessType, Membership
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from services.events.events_service import EventsService
from services.events.participants_service import ParticipantsService


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def participants_service():
    return ParticipantsService()


@pytest.fixture
def event_repository():
    return EventRepository()


@pytest.fixture
def participant_repository():
    return ParticipantRepository()


@pytest.fixture
def membership_repository():
    return MembershipRepository()


def _event_payload(**overrides):
    date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
    payload = {
        "title": f"Integration Participants {uuid4().hex[:8]}",
        "date": date_value,
        "startTime": "21:00",
        "endTime": "23:00",
        "location": "Integration Hall",
        "locationHint": "Ingresso principale",
        "price": 10.0,
        "fee": 1.0,
        "status": "active",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def create_event(events_service):
    created = []

    def _create(**overrides):
        payload = _event_payload(**overrides)
        dto = CreateEventRequestDTO.model_validate(payload)
        result = events_service.create_event(dto, admin_uid="admin-test")
        event_id = result.event_id
        created.append(event_id)
        return event_id

    yield _create

    for event_id in created:
        if event_id:
            events_service.delete_event(event_id, admin_uid="admin-test")


@pytest.fixture
def participant_payload(unique_email):
    return {
        "name": "Mario",
        "surname": "Rossi",
        "email": unique_email,
        "phone": "+390000000000",
        "birthdate": "01-01-1990",
        "price": 0,
    }


@pytest.fixture
def minor_participant_payload(unique_email):
    return {
        "name": "Luca",
        "surname": "Bianchi",
        "email": unique_email,
        "phone": "+390000000001",
        "birthdate": "01-01-2015",
        "price": 0,
    }


@pytest.fixture
def member_record(unique_email, membership_repository):
    membership = Membership(
        name="Mario",
        surname="Rossi",
        email=unique_email,
        phone="+390000000000",
        birthdate="01-01-1990",
        subscription_valid=True,
    )
    membership_id = membership_repository.create_from_model(membership)
    yield membership_id
    membership_repository.delete(membership_id)


@pytest.fixture
def only_members_event(create_event):
    return create_event(purchaseMode=EventPurchaseAccessType.ONLY_MEMBERS.value)
