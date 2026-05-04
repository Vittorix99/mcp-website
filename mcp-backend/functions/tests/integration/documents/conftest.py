from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from dto.event_api import PublicEventResponseDTO
from dto.membership_api import MembershipResponseDTO
from services.events.documents_service import DocumentsService


class _InMemoryBlob:
    def __init__(self, path: str, objects: dict):
        self._path = path
        self._objects = objects
        self.public_url = f"https://storage.local/{path}"

    def upload_from_string(self, data, content_type=None):
        self._objects[self._path] = bytes(data)

    def exists(self):
        return self._path in self._objects

    def delete(self):
        self._objects.pop(self._path, None)


class _InMemoryStorage:
    def __init__(self):
        self._objects = {}

    def blob(self, path):
        return _InMemoryBlob(path, self._objects)


@pytest.fixture
def documents_service():
    # Keep document integration tests fully local (no external GCS auth/network).
    return DocumentsService(storage=_InMemoryStorage())


@pytest.fixture
def membership_dto(unique_email):
    return MembershipResponseDTO(
        name="Mario",
        surname="Rossi",
        email=unique_email,
        phone="+390000000000",
        birthdate="01-01-1990",
        subscription_valid=True,
    )


@pytest.fixture
def event_dto():
    date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
    return PublicEventResponseDTO(
        title=f"Integration Document {uuid4().hex[:8]}",
        date=date_value,
        start_time="21:00",
        end_time="23:00",
        location_hint="Ingresso principale",
    )
