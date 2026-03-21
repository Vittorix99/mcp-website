from types import SimpleNamespace

import pytest

from dto import EventParticipantDTO
from models import Event, Membership, Purchase
from services.memberships.membership_reports_service import MembershipReportsService
from errors.service_errors import NotFoundError, ValidationError


class _DummyEventRepo:
    def __init__(self, model=None):
        self.model = model

    def get_model(self, event_id):
        return self.model


class _DummySettingsRepo:
    def __init__(self, fee=None):
        self.fee = fee

    def get_price_by_year(self, year):
        return self.fee


class _DummyPurchaseRepo:
    def __init__(self, purchases=None):
        self.purchases = purchases or []

    def list_models_by_ref_id(self, event_id):
        return self.purchases


class _DummyMembershipRepo:
    def __init__(self, by_purchase=None, by_ids=None):
        self.by_purchase = by_purchase or {}
        self.by_ids = by_ids or {}

    def list_by_purchase_ids(self, purchase_ids):
        result = []
        for pid in purchase_ids:
            result.extend(self.by_purchase.get(pid, []))
        return result

    def list_by_ids(self, membership_ids):
        return [self.by_ids[mid] for mid in membership_ids if mid in self.by_ids]


class _DummyParticipantRepo:
    def __init__(self, participants=None):
        self.participants = participants or []

    def stream(self, event_id):
        return iter(self.participants)


def _make_service():
    service = MembershipReportsService()
    return service


def _make_membership(mid, purchase_id=None, start_date="2026-01-01", name="Mario"):
    membership = Membership(
        name=name,
        surname="Rossi",
        email=f"{mid}@example.com",
        start_date=start_date,
        purchase_id=purchase_id,
    )
    membership.id = mid
    return membership


def _make_purchase(pid, net_amount):
    purchase = Purchase(net_amount=str(net_amount))
    purchase.id = pid
    purchase.ref_id = "evt-1"
    return purchase


def test_get_memberships_report_missing_event_id():
    """Rejects missing event_id."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.get_memberships_report("")


def test_get_memberships_report_event_not_found():
    """Raises when event is missing."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=None)
    with pytest.raises(NotFoundError):
        service.get_memberships_report("evt-1")


def test_get_memberships_report_happy_path():
    """Builds membership report with new/existing associates."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Event", date="13-02-2026"))
    service.settings_repository = _DummySettingsRepo(fee=10)

    purchase1 = _make_purchase("pur-1", 50)
    purchase2 = _make_purchase("pur-2", 20)
    service.purchase_repository = _DummyPurchaseRepo(purchases=[purchase1, purchase2])

    mem1 = _make_membership("mem-1", purchase_id="pur-1", start_date="2026-01-01", name="A")
    mem2 = _make_membership("mem-2", purchase_id="pur-2", start_date="2026-02-01", name="B")
    mem3 = _make_membership("mem-3", purchase_id=None, start_date="2025-12-31", name="C")
    service.membership_repository = _DummyMembershipRepo(
        by_purchase={"pur-1": [mem1], "pur-2": [mem2]},
        by_ids={"mem-3": mem3},
    )

    participant = EventParticipantDTO(event_id="evt-1", membership_id="mem-3", purchase_id="pur-1")
    service.participant_repository = _DummyParticipantRepo(participants=[participant])

    payload = service.get_memberships_report("evt-1")

    assert payload["new_associates_count"] == 2
    assert payload["existing_associates_count"] == 1
    assert payload["total_net_collected"] == 70.0
    assert len(payload["rows"]) == 3
