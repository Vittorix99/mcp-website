import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from dto.event_api import CreateEventRequestDTO
from dto.preorder import CheckoutParticipantDTO
from models import EventPurchaseAccessType, Membership
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.order_repository import OrderRepository
from services.events.events_service import EventsService


@pytest.fixture(scope="session")
def paypal_env():
    if not os.environ.get("PAYPAL_CLIENT_ID") or not os.environ.get("PAYPAL_CLIENT_SECRET"):
        pytest.skip("PayPal credentials are not set for integration tests")
    return True


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def event_repository():
    return EventRepository()


@pytest.fixture
def order_repository():
    return OrderRepository()


@pytest.fixture
def membership_repository():
    return MembershipRepository()


@pytest.fixture
def membership_settings_repository():
    return MembershipSettingsRepository()


def _event_payload(**overrides):
    date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
    payload = {
        "title": f"Integration Payment {uuid4().hex[:8]}",
        "date": date_value,
        "startTime": "21:00",
        "endTime": "23:00",
        "location": "Integration Hall",
        "locationHint": "Ingresso principale",
        "price": 12.0,
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
def participant(unique_email):
    return CheckoutParticipantDTO(
        name="Mario",
        surname="Rossi",
        email=unique_email,
        phone="+390000000000",
        birthdate="01-01-1990",
    )


@pytest.fixture
def underage_participant(unique_email):
    return CheckoutParticipantDTO(
        name="Luca",
        surname="Bianchi",
        email=unique_email,
        phone="+390000000000",
        birthdate="01-01-2010",
    )


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
def ensure_membership_fee(membership_settings_repository):
    from google.cloud import firestore
    from config.firebase_config import db

    year = str(datetime.now(timezone.utc).year)
    previous = membership_settings_repository.get_price_by_year(year)
    membership_settings_repository.set_price_by_year(year, 20.0)
    yield 20.0
    doc_ref = db.collection("membership_settings").document("price")
    if previous is None:
        doc_ref.update({f"price_by_year.{year}": firestore.DELETE_FIELD})
    else:
        doc_ref.update({f"price_by_year.{year}": previous})
