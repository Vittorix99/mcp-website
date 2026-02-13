import logging
from types import SimpleNamespace

import pytest

from dto import EventParticipantDTO
from dto.preorder import CheckoutParticipantDTO
from models import Event, EventParticipant, Membership, PaymentMethod, EventPurchaseAccessType
from services.participants_service import ParticipantsService
from services.service_errors import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from domain.participant_rules import ParticipantCheckResult


class _DummyEventRepo:
    def __init__(self, model=None, raw_type=None):
        self.model = model
        self.raw_type = raw_type

    def get_model(self, event_id):
        return self.model

    def get_raw_type(self, event_id):
        return self.raw_type


class _DummyMembershipRepo:
    def __init__(self):
        self.by_email = {}
        self.by_phone = {}
        self.updated = []
        self.created = []
        self.attended = []

    def find_model_by_email(self, email):
        return self.by_email.get(email)

    def find_model_by_phone(self, phone):
        return self.by_phone.get(phone)

    def update_from_model(self, membership_id, dto):
        self.updated.append((membership_id, dto))

    def create_from_model(self, membership):
        self.created.append(membership)
        return "mem-new"

    def add_attended_event(self, membership_id, event_id):
        self.attended.append((membership_id, event_id))
        return True


class _DummyParticipantRepo:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self._participant = None

    def list(self, event_id):
        return []

    def get(self, event_id, participant_id):
        return self._participant

    def create_from_model(self, event_id, participant):
        self.created.append((event_id, participant))
        return "part-1"

    def update(self, event_id, participant_id, payload):
        self.updated.append((event_id, participant_id, payload))
        return True

    def delete(self, event_id, participant_id):
        self.deleted.append((event_id, participant_id))


class _DummyTicketService:
    def __init__(self, result=None):
        self.result = result or {"success": True}

    def process_new_ticket(self, participant_id, participant):
        return self.result


def _make_service():
    service = ParticipantsService.__new__(ParticipantsService)
    service.logger = logging.getLogger("ParticipantsServiceTest")
    service.event_repository = _DummyEventRepo()
    service.membership_repository = _DummyMembershipRepo()
    service.participant_repository = _DummyParticipantRepo()
    service.allowed_payment_methods = {method.value for method in PaymentMethod}
    service.ticket_service = _DummyTicketService()
    return service


def _participant_payload(**overrides):
    payload = {
        "event_id": "evt-1",
        "name": "Mario",
        "surname": "Rossi",
        "email": "mario@example.com",
        "phone": "+390000000000",
        "birthdate": "01-01-1990",
        "payment_method": "cash",
        "price": 10,
    }
    payload.update(overrides)
    return payload


def test_get_by_id_not_found():
    """Raises when participant does not exist."""
    service = _make_service()
    service.participant_repository._participant = None
    with pytest.raises(NotFoundError):
        service.get_by_id("evt-1", "part-1")


def test_create_requires_event_id():
    """Rejects missing event_id on creation."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.create({"name": "Mario"})


def test_create_rejects_minors():
    """Rejects participants under 18."""
    service = _make_service()
    payload = _participant_payload(birthdate="01-01-2015")
    with pytest.raises(ForbiddenError):
        service.create(payload)


def test_create_rejects_invalid_payment_method():
    """Rejects invalid payment_method."""
    service = _make_service()
    payload = _participant_payload(payment_method="invalid")
    with pytest.raises(ValidationError):
        service.create(payload)


def test_create_conflict_on_active_membership():
    """Prevents membership_included when user is already an active member."""
    service = _make_service()
    membership = Membership(subscription_valid=True)
    membership.id = "mem-1"
    service.membership_repository.by_email["mario@example.com"] = membership
    payload = _participant_payload(membership_included=True)
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    with pytest.raises(ConflictError):
        service.create(payload)


def test_create_upgrades_existing_inactive_membership():
    """Upgrades existing inactive membership when membership_included is true."""
    service = _make_service()
    membership = Membership(subscription_valid=False, name="Mario", surname="Rossi")
    membership.id = "mem-1"
    service.membership_repository.by_email["mario@example.com"] = membership
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    payload = _participant_payload(membership_included=True)

    result = service.create(payload)

    assert result["id"] == "part-1"
    assert service.membership_repository.updated
    assert service.participant_repository.created


def test_create_creates_membership_when_missing():
    """Creates a new membership when membership_included and no membership exists."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    payload = _participant_payload(membership_included=True)

    result = service.create(payload)

    assert result["id"] == "part-1"
    assert service.membership_repository.created


def test_create_event_not_found():
    """Fails when target event does not exist."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=None)
    payload = _participant_payload()
    with pytest.raises(NotFoundError):
        service.create(payload)


def test_create_requires_active_membership_for_members_only_events():
    """Rejects non-members for members-only events."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(
        model=Event(
            title="Test",
            date="13-02-2026",
            purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
        )
    )
    payload = _participant_payload(membership_included=False)
    with pytest.raises(ForbiddenError):
        service.create(payload)


def test_update_rejects_payment_method_change_for_purchase():
    """Blocks payment_method changes for website purchases."""
    service = _make_service()
    participant = EventParticipantDTO(event_id="evt-1", purchase_id="pur-1")
    service.participant_repository._participant = participant
    with pytest.raises(ValidationError):
        service.update("evt-1", "part-1", {"payment_method": "cash"})


def test_update_rejects_price_change_for_purchase():
    """Blocks price changes when a purchase already exists."""
    service = _make_service()
    participant = EventParticipantDTO(event_id="evt-1", purchase_id="pur-1")
    service.participant_repository._participant = participant
    with pytest.raises(ValidationError):
        service.update("evt-1", "part-1", {"price": 10})


def test_update_happy_path():
    """Updates a participant when validations pass."""
    service = _make_service()
    participant = EventParticipantDTO(event_id="evt-1")
    service.participant_repository._participant = participant
    result = service.update("evt-1", "part-1", {"name": "Luigi"})
    assert result["message"]
    assert service.participant_repository.updated


def test_delete_happy_path():
    """Deletes a participant."""
    service = _make_service()
    result = service.delete("evt-1", "part-1")
    assert result["message"]
    assert service.participant_repository.deleted == [("evt-1", "part-1")]


def test_send_ticket_not_found():
    """Raises when participant is missing for ticket sending."""
    service = _make_service()
    service.participant_repository._participant = None
    with pytest.raises(NotFoundError):
        service.send_ticket("evt-1", "part-1")


def test_send_ticket_external_error():
    """Raises when ticket service fails."""
    service = _make_service()
    service.participant_repository._participant = EventParticipantDTO(event_id="evt-1")
    service.ticket_service = _DummyTicketService(result={"success": False, "error": "boom"})
    with pytest.raises(ExternalServiceError):
        service.send_ticket("evt-1", "part-1")


def test_send_ticket_happy_path():
    """Returns success when ticket is sent."""
    service = _make_service()
    service.participant_repository._participant = EventParticipantDTO(event_id="evt-1")
    result = service.send_ticket("evt-1", "part-1")
    assert "Ticket inviato" in result["message"]


def test_check_participants_requires_inputs():
    """Rejects missing eventId or participants list."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.check_participants("", [])


def test_check_participants_event_not_found():
    """Raises when event is missing."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=None)
    with pytest.raises(NotFoundError):
        service.check_participants("evt-1", [_participant_payload()])


def test_check_participants_validation_error(monkeypatch):
    """Surfaces validation details from basic checks."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    monkeypatch.setattr(
        "services.participants_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(errors=["err"]),
    )
    with pytest.raises(ValidationError) as exc:
        service.check_participants("evt-1", [_participant_payload()])
    assert exc.value.details == ["err"]


def test_check_participants_on_request_returns_lists(monkeypatch):
    """Returns members/nonMembers for on-request events."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(
        model=Event(title="Test", date="13-02-2026", purchase_mode=EventPurchaseAccessType.ON_REQUEST)
    )
    result = ParticipantCheckResult(members=["A"], non_members=["B"])
    monkeypatch.setattr("services.participants_service.run_basic_checks", lambda *args, **kwargs: result)
    payload = service.check_participants("evt-1", [_participant_payload()])
    assert payload["members"] == ["A"]
    assert payload["nonMembers"] == ["B"]


def test_check_participants_members_only_rejects_non_members(monkeypatch):
    """Rejects non-members for members-only events."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(
        model=Event(
            title="Test",
            date="13-02-2026",
            purchase_mode=EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS,
        )
    )
    result = ParticipantCheckResult(non_members=["B"])
    monkeypatch.setattr("services.participants_service.run_basic_checks", lambda *args, **kwargs: result)
    with pytest.raises(ValidationError) as exc:
        service.check_participants("evt-1", [_participant_payload()])
    assert "validation_error" in str(exc.value)


def test_check_participants_happy_path(monkeypatch):
    """Returns valid True when checks pass."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    monkeypatch.setattr(
        "services.participants_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )
    payload = service.check_participants("evt-1", [_participant_payload()])
    assert payload == {"valid": True}
