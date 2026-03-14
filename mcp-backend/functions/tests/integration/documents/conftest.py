from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from dto import EventDTO, MembershipDTO
from services.events.documents_service import DocumentsService


@pytest.fixture
def documents_service():
    return DocumentsService()


@pytest.fixture
def membership_dto(unique_email):
    return MembershipDTO.from_payload(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": unique_email,
            "phone": "+390000000000",
            "birthdate": "01-01-1990",
            "subscription_valid": True,
        }
    )


@pytest.fixture
def event_dto():
    date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
    return EventDTO.from_payload(
        {
            "title": f"Integration Document {uuid4().hex[:8]}",
            "date": date_value,
            "startTime": "21:00",
            "endTime": "23:00",
            "location": "Integration Hall",
            "locationHint": "Ingresso principale",
        }
    )
