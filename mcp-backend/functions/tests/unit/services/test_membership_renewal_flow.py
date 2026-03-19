"""
Unit tests for the membership renewal flow triggered when a previous-year member
buys a ticket for a new ONLY_MEMBERS event.

Flow under test:
  1. Event ONLY_MEMBERS is created.
  2. Participant has an existing membership with start_date in the previous year.
  3. _is_valid_member() returns False  →  participant lands in membership_targets (not lookup).
  4. create_memberships_for_targets() finds the existing record, updates it:
       start_date        = capture_time (current year)
       end_date          = 31-12-YYYY
       membership_sent   = False
       send_card_on_create = True   ← triggers pass creation + email dispatch
  5. After capture, start_date reflects the current year → member appears in 2026.
"""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from domain.participant_rules import _is_valid_member, run_basic_checks
from dto import CheckoutParticipantDTO, MembershipDTO, OrderCaptureDTO, PreOrderCartItemDTO, PreOrderDTO
from models import (
    Event,
    EventOrder,
    EventPurchaseAccessType,
    Membership,
    MembershipRef,
    PurchaseTypes,
)
from services.payments.event_payment_service import EventPaymentService


# ---------------------------------------------------------------------------
# Shared dummy infrastructure (mirrors test_event_payment_service.py)
# ---------------------------------------------------------------------------

class _DummyOrdersController:
    def __init__(self, create_body=None):
        self._create_body = create_body or {"id": "order-1", "status": "CREATED"}

    def orders_create(self, payload):
        return SimpleNamespace(status_code=201, body=self._create_body)

    def orders_capture(self, payload):
        return SimpleNamespace(status_code=200, body=_capture_payload())


class _DummyOrderRepo:
    def __init__(self, order_data=None):
        self.saved = []
        self.deleted = []
        self.status_updates = []
        self._order_data = order_data

    def save(self, order_id, order):
        self.saved.append((order_id, order))

    def get(self, order_id):
        return self._order_data

    def delete(self, order_id):
        self.deleted.append(order_id)

    def update_status(self, order_id, status):
        self.status_updates.append((order_id, status))


class _DummyEventRepo:
    def __init__(self, model=None):
        self.model = model

    def get_model(self, event_id):
        return self.model


class _DummyMembershipSettingsRepo:
    def get_price_by_year(self, year):
        return 20.0


class _DummyPurchaseRepo:
    def __init__(self):
        self.created = []
        self.updated = []

    def create(self, purchase):
        self.created.append(purchase)
        return "pur-renewal-1"

    def update_participants(self, purchase_id, count, membership_ids):
        self.updated.append((purchase_id, count, membership_ids))


class _DummyMembershipRepo:
    def __init__(self, existing: Membership = None):
        self.existing = existing
        self.updated = []
        self.appended = []
        self.created = []
        self.attended = []

    def find_model_by_email(self, email):
        if self.existing and self.existing.email == email:
            return self.existing
        return None

    def update_from_model(self, membership_id, dto):
        self.updated.append((membership_id, dto))

    def append_purchase(self, membership_id, purchase_id):
        self.appended.append((membership_id, purchase_id))

    def create_from_model(self, membership):
        self.created.append(membership)
        return "mem-new"

    def add_attended_event_and_purchase(self, membership_id, event_id, purchase_id):
        self.attended.append((membership_id, event_id, purchase_id))


class _DummyParticipantRepo:
    def __init__(self):
        self.created = []
        self.contacted = []

    def create(self, event_id, payload):
        self.created.append((event_id, payload))
        return "part-1"

    def any_with_contacts(self, event_id, emails, phones):
        return False


def _make_service(existing_membership: Membership = None):
    service = EventPaymentService.__new__(EventPaymentService)
    service.debug = False
    service.orders_controller = _DummyOrdersController()
    service.event_repository = _DummyEventRepo()
    service.membership_repository = _DummyMembershipRepo(existing=existing_membership)
    service.membership_settings_repository = _DummyMembershipSettingsRepo()
    service.order_repository = _DummyOrderRepo()
    service.purchase_repository = _DummyPurchaseRepo()
    service.participant_repository = _DummyParticipantRepo()
    return service


def _previous_year_membership(email: str) -> Membership:
    """A membership whose start_date is in the previous year."""
    prev_year = datetime.now(timezone.utc).year - 1
    return Membership(
        id="mem-prev-year",
        name="Mario",
        surname="Rossi",
        email=email,
        phone="+390000000000",
        birthdate="01-01-1990",
        start_date=f"{prev_year}-09-05T22:55:43Z",
        end_date=f"31-12-{prev_year}",
        subscription_valid=True,
        membership_sent=True,
        send_card_on_create=False,
        membership_type="event",
    )


def _current_year_membership(email: str) -> Membership:
    """A membership whose start_date is in the current year."""
    curr_year = datetime.now(timezone.utc).year
    return Membership(
        id="mem-curr-year",
        name="Mario",
        surname="Rossi",
        email=email,
        phone="+390000000000",
        birthdate="01-01-1990",
        start_date=f"{curr_year}-03-01T10:00:00Z",
        end_date=f"31-12-{curr_year}",
        subscription_valid=True,
        membership_sent=True,
        send_card_on_create=False,
        membership_type="event",
    )


def _participant(email: str = "mario@example.com") -> CheckoutParticipantDTO:
    return CheckoutParticipantDTO(
        name="Mario",
        surname="Rossi",
        email=email,
        phone="+390000000000",
        birthdate="01-01-1990",
    )


def _capture_payload(order_id: str = "order-1") -> dict:
    curr_year = datetime.now(timezone.utc).year
    return {
        "id": order_id,
        "status": "COMPLETED",
        "payment_source": {
            "paypal": {
                "name": {"given_name": "Mario", "surname": "Rossi"},
                "email_address": "mario@example.com",
            }
        },
        "purchase_units": [
            {
                "payments": {
                    "captures": [
                        {
                            "id": "CAP-RENEWAL",
                            "status": "COMPLETED",
                            "final_capture": True,
                            "amount": {"value": "32.00", "currency_code": "EUR"},
                            "create_time": f"{curr_year}-03-19T10:00:00Z",
                            "seller_receivable_breakdown": {
                                "paypal_fee": {"value": "1.0"},
                                "net_amount": {"value": "31.0"},
                            },
                        }
                    ]
                }
            }
        ],
    }


# ---------------------------------------------------------------------------
# 1. _is_valid_member: previous-year membership is expired
# ---------------------------------------------------------------------------

def test_is_valid_member_previous_year_returns_false():
    """A membership from a previous year must not be considered active."""
    m = _previous_year_membership("test@example.com")
    assert _is_valid_member(m) is False


def test_is_valid_member_current_year_returns_true():
    """A membership from the current year with subscription_valid=True is active."""
    m = _current_year_membership("test@example.com")
    assert _is_valid_member(m) is True


def test_is_valid_member_no_start_date_falls_back_to_subscription_valid():
    """If start_date is missing, fall back to subscription_valid."""
    m = Membership(
        name="A",
        surname="B",
        email="a@example.com",
        subscription_valid=True,
    )
    assert _is_valid_member(m) is True


def test_is_valid_member_no_start_date_and_invalid_subscription():
    """No start_date and subscription_valid=False → not a valid member."""
    m = Membership(
        name="A",
        surname="B",
        email="a@example.com",
        subscription_valid=False,
    )
    assert _is_valid_member(m) is False


# ---------------------------------------------------------------------------
# 2. run_basic_checks: previous-year member lands in non_members
# ---------------------------------------------------------------------------

def test_run_basic_checks_previous_year_member_is_non_member():
    """
    A participant with an existing membership from the previous year must be
    classified as non_member, so the renewal flow can be triggered.
    """
    email = "mario@example.com"
    prev_membership = _previous_year_membership(email)

    membership_repo = _DummyMembershipRepo(existing=prev_membership)
    participant_repo = _DummyParticipantRepo()

    event = Event(title="Test Event", date="19-03-2026")
    p = _participant(email)

    result = run_basic_checks(
        "evt-1",
        [p],
        event,
        participant_repository=participant_repo,
        membership_repository=membership_repo,
    )

    assert email in result.non_members or any(email in s for s in result.non_members)
    assert email not in result.membership_docs
    assert not result.errors


def test_run_basic_checks_current_year_member_is_member():
    """A participant with a current-year membership must be classified as member."""
    email = "mario@example.com"
    curr_membership = _current_year_membership(email)

    membership_repo = _DummyMembershipRepo(existing=curr_membership)
    participant_repo = _DummyParticipantRepo()

    event = Event(title="Test Event", date="19-03-2026")
    p = _participant(email)

    result = run_basic_checks(
        "evt-1",
        [p],
        event,
        participant_repository=participant_repo,
        membership_repository=membership_repo,
    )

    assert email in result.membership_docs
    assert not result.errors


# ---------------------------------------------------------------------------
# 3. create_order_event: previous-year member becomes a membership_target
# ---------------------------------------------------------------------------

def test_create_order_event_previous_year_member_is_target(monkeypatch):
    """
    Step 1+2 of the renewal flow: an ONLY_MEMBERS event receives a participant
    who was a member last year. The participant must end up in membership_targets
    (not in membership_lookup), triggering the renewal during capture.
    """
    email = "mario@example.com"
    prev_membership = _previous_year_membership(email)

    service = _make_service(existing_membership=prev_membership)
    event = Event(
        title="Renewal Event",
        date="19-03-2026",
        price=12.0,
        fee=0.0,
        purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
    )
    service.event_repository = _DummyEventRepo(model=event)
    service.orders_controller = _DummyOrdersController()

    monkeypatch.setattr(
        "services.payments.event_payment_service.ApiHelper.json_serialize",
        lambda body: json.dumps(body),
    )

    # run_basic_checks uses the real _DummyMembershipRepo / _DummyParticipantRepo
    # injected via monkeypatch so the previous-year logic is exercised end-to-end
    from domain import participant_rules as pr

    original_run = pr.run_basic_checks

    def patched_run(event_id, participants, event_data, **kwargs):
        return original_run(
            event_id,
            participants,
            event_data,
            membership_repository=service.membership_repository,
            participant_repository=service.participant_repository,
        )

    monkeypatch.setattr("services.payments.event_payment_service.run_basic_checks", patched_run)

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant(email)])])
    result = service.create_order_event(payload)

    assert result["id"] == "order-1"
    saved_order = service.order_repository.saved[0][1]

    # The previous-year member must be in targets, not in lookup
    assert len(saved_order.membership_targets) == 1
    assert saved_order.membership_lookup == {} or email not in saved_order.membership_lookup
    assert saved_order.membership_fee == 20.0


# ---------------------------------------------------------------------------
# 4. create_memberships_for_targets: updates existing record for renewal
# ---------------------------------------------------------------------------

def test_create_memberships_for_targets_updates_existing_member():
    """
    Step 3+4: when an existing (previous-year) membership is found,
    create_memberships_for_targets must update start_date, end_date,
    and set send_card_on_create=True to trigger pass creation and email.
    """
    email = "mario@example.com"
    prev_membership = _previous_year_membership(email)

    service = _make_service(existing_membership=prev_membership)
    curr_year = datetime.now(timezone.utc).year
    capture_time = f"{curr_year}-03-19T10:00:00Z"

    refs = service.create_memberships_for_targets(
        targets=[_participant(email)],
        membership_fee=20.0,
        capture_time=capture_time,
        purchase_id="pur-1",
    )

    assert len(refs) == 1
    assert refs[0].membership_id == "mem-prev-year"
    assert refs[0].email == email

    # The existing record must have been updated, not created anew
    assert len(service.membership_repository.updated) == 1
    assert len(service.membership_repository.created) == 0

    _, update_dto = service.membership_repository.updated[0]

    # start_date must be updated to the current capture time
    assert update_dto.start_date == capture_time

    # end_date must be in the current year
    assert str(curr_year) in update_dto.end_date

    # Flags that trigger pass creation and email sending
    assert update_dto.send_card_on_create is True
    assert update_dto.membership_sent is False

    assert update_dto.subscription_valid is True


def test_create_memberships_for_targets_creates_new_when_no_existing():
    """
    A participant with no prior membership record gets a new one created,
    also with send_card_on_create=True.
    """
    email = "nuovomembro@example.com"
    service = _make_service(existing_membership=None)
    curr_year = datetime.now(timezone.utc).year
    capture_time = f"{curr_year}-03-19T10:00:00Z"

    refs = service.create_memberships_for_targets(
        targets=[_participant(email)],
        membership_fee=20.0,
        capture_time=capture_time,
        purchase_id="pur-new",
    )

    assert len(refs) == 1
    assert refs[0].membership_id == "mem-new"

    assert len(service.membership_repository.created) == 1
    assert len(service.membership_repository.updated) == 0

    created = service.membership_repository.created[0]
    assert created.send_card_on_create is True
    assert created.membership_sent is False
    assert str(curr_year) in created.end_date


# ---------------------------------------------------------------------------
# 5. Full capture flow: start_date renewed, participant registered for event
# ---------------------------------------------------------------------------

def test_capture_renews_previous_year_member_and_registers_participant(monkeypatch):
    """
    Full end-to-end unit test of the renewal capture flow:
      - The staged order contains the previous-year member in membership_targets.
      - After capture, the membership is updated with the current-year start_date.
      - send_card_on_create=True is set → pass creation and email will be triggered.
      - The participant is registered for the event with membership_included=True.
    """
    email = "mario@example.com"
    curr_year = datetime.now(timezone.utc).year
    capture_time = f"{curr_year}-03-19T10:00:00Z"
    prev_membership = _previous_year_membership(email)

    service = _make_service(existing_membership=prev_membership)

    # Build the staged order: participant is in membership_targets (not lookup)
    participant_payload = _participant(email).to_payload()
    event_order = EventOrder(
        order_id="order-renewal",
        order_status="CREATED",
        purchase_type=PurchaseTypes.EVENT,
        cart=[{"eventId": "evt-renewal"}],
        total=32.0,
        reference_id="evt-renewal",
        event_meta={},
        event_id="evt-renewal",
        participants=[participant_payload],
        event_price=12.0,
        event_fee=0.0,
        membership_targets=[participant_payload],
        membership_fee=20.0,
        purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
        membership_lookup={},
    )
    service.order_repository = _DummyOrderRepo(
        order_data=event_order.to_firestore(include_none=True)
    )

    monkeypatch.setattr(
        service,
        "capture_paypal_order",
        lambda order_id: _capture_payload(order_id),
    )
    monkeypatch.setattr(
        "services.payments.event_payment_service.ApiHelper.json_serialize",
        lambda body: json.dumps(body),
    )

    result = service.capture_order_event(OrderCaptureDTO(order_id="order-renewal"))

    assert result["purchase_id"] == "pur-renewal-1"

    # Membership must have been updated (renewed), not created from scratch
    assert len(service.membership_repository.updated) == 1
    assert len(service.membership_repository.created) == 0

    _, update_dto = service.membership_repository.updated[0]
    assert update_dto.start_date == capture_time
    assert str(curr_year) in update_dto.end_date
    assert update_dto.send_card_on_create is True
    assert update_dto.membership_sent is False

    # Participant must be registered for the event with membership_included=True
    assert len(service.participant_repository.created) == 1
    event_id_saved, part_payload = service.participant_repository.created[0]
    assert event_id_saved == "evt-renewal"
    assert part_payload.get("membership_included") is True

    # The staging order must have been deleted after capture
    assert "order-renewal" in service.order_repository.deleted


# ---------------------------------------------------------------------------
# 6. Regression: current-year member is NOT re-enrolled as a target
# ---------------------------------------------------------------------------

def test_create_order_event_current_year_member_is_not_target(monkeypatch):
    """
    Regression guard: a participant who is already a current-year member must
    stay in membership_lookup and must NOT appear in membership_targets.
    """
    email = "mario@example.com"
    curr_membership = _current_year_membership(email)

    service = _make_service(existing_membership=curr_membership)
    event = Event(
        title="Renewal Event",
        date="19-03-2026",
        price=12.0,
        fee=0.0,
        purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
    )
    service.event_repository = _DummyEventRepo(model=event)
    service.orders_controller = _DummyOrdersController()

    monkeypatch.setattr(
        "services.payments.event_payment_service.ApiHelper.json_serialize",
        lambda body: json.dumps(body),
    )

    from domain import participant_rules as pr
    original_run = pr.run_basic_checks

    def patched_run(event_id, participants, event_data, **kwargs):
        return original_run(
            event_id,
            participants,
            event_data,
            membership_repository=service.membership_repository,
            participant_repository=service.participant_repository,
        )

    monkeypatch.setattr("services.payments.event_payment_service.run_basic_checks", patched_run)

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant(email)])])
    result = service.create_order_event(payload)

    saved_order = service.order_repository.saved[0][1]

    # Current-year member → in lookup, not in targets
    assert email in saved_order.membership_lookup
    assert len(saved_order.membership_targets) == 0
    assert saved_order.membership_fee is None
