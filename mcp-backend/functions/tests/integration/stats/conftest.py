from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from models import ContactMessage, EventParticipant, Membership, PaymentMethod, Purchase, PurchaseTypes
from repositories.event_repository import EventRepository
from repositories.message_repository import MessageRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.events.events_service import EventsService
from dto import EventDTO


@pytest.fixture
def stats_repos():
    return {
        "events": EventRepository(),
        "memberships": MembershipRepository(),
        "purchases": PurchaseRepository(),
        "participants": ParticipantRepository(),
        "messages": MessageRepository(),
    }


@pytest.fixture
def create_stats_fixtures(stats_repos):
    created = {"events": [], "memberships": [], "purchases": [], "participants": [], "messages": []}
    events_service = EventsService()

    def _create():
        date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
        event_dto = EventDTO.from_payload(
            {
                "title": f"Stats Event {uuid4().hex[:8]}",
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
        event_id = events_service.create_event(event_dto, admin_uid="admin-test").get("eventId")
        created["events"].append(event_id)

        membership = Membership(
            name="Mario",
            surname="Rossi",
            email=f"mcpweb.testing+stats_{uuid4().hex[:8]}@gmail.com",
            phone="+390000000000",
            birthdate="01-01-1990",
            subscription_valid=True,
            start_date=datetime.now(timezone.utc).isoformat(),
        )
        membership_id = stats_repos["memberships"].create_from_model(membership)
        created["memberships"].append(membership_id)

        purchase = Purchase(
            payer_name="Mario",
            payer_surname="Rossi",
            payer_email=membership.email,
            amount_total="10.00",
            currency="EUR",
            transaction_id=f"txn-{uuid4().hex[:8]}",
            order_id=f"order-{uuid4().hex[:8]}",
            status="COMPLETED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            purchase_type=PurchaseTypes.EVENT,
            ref_id=event_id,
            payment_method="website",
            capture_status="COMPLETED",
        )
        purchase_id = stats_repos["purchases"].create_from_model(purchase)
        created["purchases"].append(purchase_id)

        participant = EventParticipant(
            event_id=event_id,
            name="Mario",
            surname="Rossi",
            email=membership.email,
            phone="+390000000000",
            birthdate="01-01-1990",
            payment_method=PaymentMethod.WEBSITE,
            price=10.0,
            created_at=datetime.now(timezone.utc),
        )
        participant_id = stats_repos["participants"].create_from_model(event_id, participant)
        created["participants"].append((event_id, participant_id))

        message = ContactMessage(
            name="Mario",
            email=membership.email,
            message="Stats integration message",
            answered=False,
            timestamp=datetime.now(timezone.utc),
        )
        message_id = stats_repos["messages"].create_from_model(message)
        created["messages"].append(message_id)

        return created

    yield _create

    for message_id in created["messages"]:
        stats_repos["messages"].delete(message_id)
    for event_id, participant_id in created["participants"]:
        stats_repos["participants"].delete(event_id, participant_id)
    for purchase_id in created["purchases"]:
        stats_repos["purchases"].delete(purchase_id)
    for membership_id in created["memberships"]:
        stats_repos["memberships"].delete(membership_id)
    for event_id in created["events"]:
        events_service.delete_event(event_id, admin_uid="admin-test")
