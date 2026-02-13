from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from dto import EventDTO, MembershipDTO
from models import Purchase, PurchaseTypes
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.purchase_repository import PurchaseRepository
from services.events_service import EventsService
from services.memberships_service import MembershipsService
from services.service_errors import NotFoundError


@pytest.fixture
def memberships_service():
    return MembershipsService()


@pytest.fixture
def membership_repository():
    return MembershipRepository()


@pytest.fixture
def purchase_repository():
    return PurchaseRepository()


@pytest.fixture
def event_repository():
    return EventRepository()


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def membership_payload(unique_email):
    suffix = str(uuid4().int)[-10:]
    phone = f"+39{suffix}"
    return {
        "name": "Mario",
        "surname": "Rossi",
        "email": unique_email,
        "phone": phone,
        "birthdate": "01-01-1990",
        "membership_type": "manual",
    }


@pytest.fixture
def minor_membership_payload(unique_email):
    suffix = str(uuid4().int)[-10:]
    phone = f"+39{suffix}"
    return {
        "name": "Luca",
        "surname": "Bianchi",
        "email": unique_email,
        "phone": phone,
        "birthdate": "01-01-2015",
        "membership_type": "manual",
    }


@pytest.fixture
def create_membership(memberships_service):
    created = []

    def _create(payload):
        dto = MembershipDTO.from_payload(payload)
        result = memberships_service.create(dto)
        membership_id = result.get("id")
        created.append(membership_id)
        return membership_id

    yield _create

    for membership_id in created:
        if membership_id:
            try:
                memberships_service.delete(membership_id)
            except NotFoundError:
                pass


@pytest.fixture
def create_purchase(purchase_repository):
    created = []

    def _create(**overrides):
        suffix = uuid4().hex[:8]
        purchase = Purchase(
            payer_name="Mario",
            payer_surname="Rossi",
            payer_email=f"mcpweb.testing+purchase_{suffix}@gmail.com",
            amount_total="10.00",
            currency="EUR",
            transaction_id=f"txn-{suffix}",
            order_id=f"order-{suffix}",
            status="COMPLETED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            purchase_type=PurchaseTypes.EVENT,
            ref_id=f"event-{suffix}",
            payment_method="website",
            capture_status="COMPLETED",
        )
        for key, value in overrides.items():
            setattr(purchase, key, value)
        purchase_id = purchase_repository.create_from_model(purchase)
        created.append(purchase_id)
        return purchase_id

    yield _create

    for purchase_id in created:
        purchase_repository.delete(purchase_id)


@pytest.fixture
def create_event(events_service):
    created = []

    def _create():
        date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
        dto = EventDTO.from_payload(
            {
                "title": f"Integration Event {uuid4().hex[:8]}",
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
