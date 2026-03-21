from datetime import datetime
from uuid import uuid4

import pytest

from dto import EventDTO
from repositories.event_repository import EventRepository
from services.events.events_service import EventsService


@pytest.fixture
def event_repository():
    return EventRepository()


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def base_event_payload():
    today = datetime.now().strftime("%d-%m-%Y")
    suffix = uuid4().hex[:8]
    return {
        "title": f"Integration Event {suffix}",
        "date": today,
        "startTime": "21:00",
        "endTime": "23:00",
        "location": "Integration Hall",
        "locationHint": "Near the main entrance",
        "price": 10.0,
        "fee": 1.5,
        "purchaseMode": "PUBLIC",
    }


@pytest.fixture
def event_dto(base_event_payload):
    return EventDTO.from_payload(base_event_payload)
