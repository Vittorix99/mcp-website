from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from dto.event_api import CreateEventRequestDTO
from models import EventParticipant, Membership, PaymentMethod
from models.event_location import EventLocation
from repositories.event_location_repository import EventLocationRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.events.events_service import EventsService


@pytest.fixture
def member_email(unique_email):
    return unique_email


@pytest.fixture(autouse=True)
def mock_member_auth(monkeypatch, member_email):
    """Bypass Firebase token verification: inject member_email into every request."""
    import api.decorators as _dec
    monkeypatch.setattr(
        _dec.fb_auth,
        "verify_id_token",
        lambda _token: {"uid": "member-test-uid", "email": member_email},
    )


@pytest.fixture(autouse=True)
def mock_sender_service(monkeypatch):
    """Prevent real HTTP calls to the Sender mailing service."""
    from api.member import member_api as _member_api
    mock = MagicMock()
    monkeypatch.setattr(_member_api.member_service, "sender_service", mock)


@pytest.fixture
def membership_repository():
    return MembershipRepository()


@pytest.fixture
def participant_repository():
    return ParticipantRepository()


@pytest.fixture
def purchase_repository():
    return PurchaseRepository()


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def create_membership(membership_repository, member_email):
    created = []

    def _create(**overrides):
        membership = Membership(
            name=overrides.get("name", "Mario"),
            surname=overrides.get("surname", "Rossi"),
            email=member_email,
            phone=overrides.get("phone", "+390123456789"),
            birthdate="01-01-1990",
            subscription_valid=overrides.get("subscription_valid", True),
            start_date=overrides.get("start_date", datetime.now(timezone.utc).isoformat()),
            end_date=overrides.get("end_date", (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()),
            newsletter_consent=overrides.get("newsletter_consent", True),
            attended_events=overrides.get("attended_events", []),
            purchases=overrides.get("purchases", []),
        )
        membership_id = membership_repository.create_from_model(membership)
        created.append(membership_id)
        return membership_id

    yield _create

    for membership_id in created:
        try:
            membership_repository.delete(membership_id)
        except Exception:
            pass


@pytest.fixture
def create_event(events_service):
    created = []

    def _create():
        date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
        dto = CreateEventRequestDTO.model_validate({
            "title": f"Member Test Event {uuid4().hex[:8]}",
            "date": date_value,
            "startTime": "21:00",
            "endTime": "23:00",
            "locationHint": "Ingresso principale",
            "price": 10.0,
            "fee": 1.0,
            "status": "active",
        })
        result = events_service.create_event(dto, admin_uid="admin-test")
        event_id = result.event_id
        created.append(event_id)
        return event_id

    yield _create

    for event_id in created:
        try:
            events_service.delete_event(event_id, admin_uid="admin-test")
        except Exception:
            pass


@pytest.fixture
def create_participant(participant_repository, member_email):
    created = []

    def _create(event_id: str, membership_id: str):
        participant = EventParticipant(
            event_id=event_id,
            name="Mario",
            surname="Rossi",
            email=member_email,
            phone="+390123456789",
            birthdate="01-01-1990",
            payment_method=PaymentMethod.WEBSITE,
            membership_id=membership_id,
        )
        participant_id = participant_repository.create_from_model(event_id, participant)
        created.append((event_id, participant_id))
        return participant_id

    yield _create

    for event_id, participant_id in created:
        try:
            participant_repository.delete(event_id, participant_id)
        except Exception:
            pass


@pytest.fixture
def seed_location():
    location_repo = EventLocationRepository()
    seeded = []

    def _seed(event_id: str, published: bool = True):
        location = EventLocation(
            label="Warehouse 23",
            maps_url="https://maps.google.com/?q=test",
            maps_embed_url="https://maps.google.com/embed?q=test",
            address="Via Test 1, Milano",
            message="Porta il biglietto",
            published=published,
        )
        location_repo.upsert_all(event_id, location)
        location_repo.set_published(event_id, published)
        seeded.append(event_id)

    yield _seed

    for event_id in seeded:
        try:
            from config.firebase_config import db
            db.collection("event_locations").document(event_id).delete()
        except Exception:
            pass
