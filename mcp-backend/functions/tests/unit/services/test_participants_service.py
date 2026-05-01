import logging
from types import SimpleNamespace

import pytest
from pydantic import ValidationError as PydanticValidationError

from dto.participant_api import (
    CheckoutParticipantRequestDTO,
    ParticipantCreateRequestDTO,
    ParticipantUpdateRequestDTO,
    SendOmaggioEmailsRequestDTO,
)
from models import Event, EventParticipant, EventPurchaseAccessType, Membership, PaymentMethod
from services.events.participants_service import ParticipantsService
from errors.service_errors import (
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
        self.by_id = {}
        self.updated = []
        self.created = []
        self.attended = []

    def find_by_email(self, email):
        return self.by_email.get(email)

    def find_by_phone(self, phone):
        return self.by_phone.get(phone)

    def update_from_model(self, membership_id, membership):
        self.updated.append((membership_id, membership))

    def create_from_model(self, membership):
        self.created.append(membership)
        return "mem-new"

    def add_attended_event(self, membership_id, event_id):
        self.attended.append((membership_id, event_id))
        return True

    def get(self, membership_id):
        return self.by_id.get(membership_id)

    def get_model(self, membership_id):
        return self.get(membership_id)


class _DummyParticipantRepo:
    def __init__(self):
        self.created = []
        self.updated = []
        self.membership_updates = []
        self.deleted = []
        self._participant = None
        self.list_items = []

    def list(self, event_id):
        return list(self.list_items)

    def get(self, event_id, participant_id):
        return self._participant

    def create_from_model(self, event_id, participant):
        self.created.append((event_id, participant))
        return "part-1"

    def update_from_model(self, event_id, participant_id, participant):
        self.updated.append((event_id, participant_id, participant))
        return True

    def delete(self, event_id, participant_id):
        self.deleted.append((event_id, participant_id))

    def set_membership(self, event_id, participant_id, membership_id):
        self.membership_updates.append((event_id, participant_id, membership_id))


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
    service.mail_service = SimpleNamespace(send=lambda *_args, **_kwargs: True)
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


def _create_dto(**overrides):
    return ParticipantCreateRequestDTO.model_validate(_participant_payload(**overrides))


def _update_dto(**overrides):
    payload = {"event_id": "evt-1", "participant_id": "part-1"}
    payload.update(overrides)
    return ParticipantUpdateRequestDTO.model_validate(payload)


def _checkout_dto(**overrides):
    payload = {
        "name": "Mario",
        "surname": "Rossi",
        "email": "mario@example.com",
        "phone": "+390000000000",
        "birthdate": "01-01-1990",
    }
    payload.update(overrides)
    return CheckoutParticipantRequestDTO.model_validate(payload)


def _participant_model(**overrides):
    data = {"event_id": "evt-1"}
    data.update(overrides)
    participant = EventParticipant(**data)
    if "id" in overrides:
        participant.id = overrides["id"]
    return participant


def test_get_by_id_not_found():
    service = _make_service()
    service.participant_repository._participant = None
    with pytest.raises(NotFoundError):
        service.get_by_id("evt-1", "part-1")


def test_create_requires_event_id():
    with pytest.raises(PydanticValidationError):
        ParticipantCreateRequestDTO.model_validate({"name": "Mario"})


def test_create_rejects_minors():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    with pytest.raises(ForbiddenError):
        service.create(_create_dto(birthdate="01-01-2015"))


def test_create_rejects_invalid_payment_method():
    with pytest.raises(PydanticValidationError):
        _create_dto(payment_method="invalid")


def test_create_rejects_invalid_email_format():
    with pytest.raises(PydanticValidationError):
        _create_dto(email="invalid-email")


def test_create_conflict_on_active_membership():
    service = _make_service()
    membership = Membership(subscription_valid=True)
    membership.id = "mem-1"
    service.membership_repository.by_email["mario@example.com"] = membership
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    with pytest.raises(ConflictError):
        service.create(_create_dto(membership_included=True))


def test_create_upgrades_existing_inactive_membership():
    service = _make_service()
    membership = Membership(subscription_valid=False, name="Mario", surname="Rossi")
    membership.id = "mem-1"
    service.membership_repository.by_email["mario@example.com"] = membership
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))

    result = service.create(_create_dto(membership_included=True))

    assert result.id == "part-1"
    assert service.membership_repository.updated
    assert service.participant_repository.created


def test_create_creates_membership_when_missing():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))

    result = service.create(_create_dto(membership_included=True))

    assert result.id == "part-1"
    assert service.membership_repository.created


def test_create_links_explicit_membership_without_renewal():
    service = _make_service()
    membership = Membership(subscription_valid=True, name="Mario", surname="Rossi")
    membership.id = "mem-42"
    service.membership_repository.by_id["mem-42"] = membership
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))

    result = service.create(_create_dto(membership_id="mem-42", membership_included=False))

    assert result.id == "part-1"
    assert not service.membership_repository.updated
    assert not service.membership_repository.created
    _, created_participant = service.participant_repository.created[0]
    assert created_participant.membership_id == "mem-42"
    assert service.membership_repository.attended == [("mem-42", "evt-1")]


def test_create_rejects_missing_explicit_membership():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))

    with pytest.raises(NotFoundError):
        service.create(_create_dto(membership_id="mem-missing", membership_included=False))


def test_create_event_not_found():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=None)
    with pytest.raises(NotFoundError):
        service.create(_create_dto())


def test_create_allows_manual_non_member_for_members_only_events():
    service = _make_service()
    service.event_repository = _DummyEventRepo(
        model=Event(
            title="Test",
            date="13-02-2026",
            purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
        )
    )

    result = service.create(_create_dto(membership_included=False))

    assert result.id == "part-1"
    assert service.participant_repository.created


def test_create_persists_riduzione_flag():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))

    result = service.create(_create_dto(riduzione=True))

    assert result.id == "part-1"
    _, created_participant = service.participant_repository.created[0]
    assert created_participant.riduzione is True


def test_update_rejects_payment_method_change_for_purchase():
    service = _make_service()
    service.participant_repository._participant = _participant_model(purchase_id="pur-1")
    with pytest.raises(ValidationError):
        service.update("evt-1", "part-1", _update_dto(payment_method="cash"))


def test_update_rejects_price_change_for_purchase():
    service = _make_service()
    service.participant_repository._participant = _participant_model(purchase_id="pur-1")
    with pytest.raises(ValidationError):
        service.update("evt-1", "part-1", _update_dto(price=10))


def test_update_happy_path():
    service = _make_service()
    service.participant_repository._participant = _participant_model()

    result = service.update("evt-1", "part-1", _update_dto(name="Luigi"))

    assert result.message
    assert service.participant_repository.updated


def test_update_rejects_invalid_email_format():
    with pytest.raises(PydanticValidationError):
        _update_dto(email="invalid-email")


def test_update_allows_manual_membership_assignment():
    service = _make_service()
    service.participant_repository._participant = _participant_model()
    service.membership_repository.by_id["mem-42"] = Membership(name="Mario")

    result = service.update("evt-1", "part-1", _update_dto(membership_id="mem-42"))

    assert result.message
    assert service.participant_repository.updated
    assert service.participant_repository.membership_updates == [("evt-1", "part-1", "mem-42")]


def test_update_allows_manual_membership_clear():
    service = _make_service()
    service.participant_repository._participant = _participant_model(membership_id="mem-old")

    result = service.update("evt-1", "part-1", _update_dto(membership_id=None))

    assert result.message
    assert service.participant_repository.updated
    assert service.participant_repository.membership_updates == [("evt-1", "part-1", None)]


def test_update_rejects_unknown_manual_membership():
    service = _make_service()
    service.participant_repository._participant = _participant_model()

    with pytest.raises(NotFoundError):
        service.update("evt-1", "part-1", _update_dto(membership_id="mem-missing"))


def test_delete_happy_path():
    service = _make_service()
    service.participant_repository._participant = _participant_model()

    result = service.delete("evt-1", "part-1")

    assert result.message
    assert service.participant_repository.deleted == [("evt-1", "part-1")]


def test_send_ticket_not_found():
    service = _make_service()
    service.participant_repository._participant = None
    with pytest.raises(NotFoundError):
        service.send_ticket("evt-1", "part-1")


def test_send_ticket_external_error():
    service = _make_service()
    service.participant_repository._participant = _participant_model()
    service.ticket_service = _DummyTicketService(result={"success": False, "error": "boom"})
    with pytest.raises(ExternalServiceError):
        service.send_ticket("evt-1", "part-1")


def test_send_ticket_happy_path():
    service = _make_service()
    service.participant_repository._participant = _participant_model()

    result = service.send_ticket("evt-1", "part-1")

    assert "Ticket inviato" in result.message


def test_send_omaggio_emails_skips_already_sent():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026", location="Roma"))
    service.participant_repository.list_items = [
        _participant_model(id="p1", name="A", surname="One", email="a@test.com", payment_method=PaymentMethod.OMAGGIO),
        _participant_model(id="p2", name="B", surname="Two", email="b@test.com", payment_method=PaymentMethod.OMAGGIO, omaggio_email_sent=True),
    ]
    dto = SendOmaggioEmailsRequestDTO(event_id="evt-1", entry_time="22:00", skip_already_sent=True)

    result = service.send_omaggio_emails(dto)

    assert result.sent == 1
    assert result.skipped == 1
    assert result.failed == 0
    assert len(service.participant_repository.updated) == 1
    event_id, participant_id, participant = service.participant_repository.updated[0]
    assert event_id == "evt-1"
    assert participant_id == "p1"
    assert participant.omaggio_email_sent is True


def test_send_omaggio_email_single_allows_resend():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026", location="Roma"))
    service.participant_repository.list_items = [
        _participant_model(id="p2", name="B", surname="Two", email="b@test.com", payment_method=PaymentMethod.OMAGGIO, omaggio_email_sent=True),
    ]
    dto = SendOmaggioEmailsRequestDTO(
        event_id="evt-1",
        entry_time="22:00",
        participant_id="p2",
        skip_already_sent=False,
    )

    result = service.send_omaggio_emails(dto)

    assert result.mode == "single"
    assert result.sent == 1
    assert result.skipped == 0
    assert len(service.participant_repository.updated) == 1


def test_check_participants_requires_inputs():
    service = _make_service()
    with pytest.raises(ValidationError):
        service.check_participants("", [])


def test_check_participants_event_not_found():
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=None)
    with pytest.raises(NotFoundError):
        service.check_participants("evt-1", [_checkout_dto()])


def test_check_participants_validation_error(monkeypatch):
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    monkeypatch.setattr(
        "services.events.participants_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(errors=["err"]),
    )
    with pytest.raises(ValidationError) as exc:
        service.check_participants("evt-1", [_checkout_dto()])
    assert exc.value.details == ["err"]


def test_check_participants_on_request_returns_lists(monkeypatch):
    service = _make_service()
    service.event_repository = _DummyEventRepo(
        model=Event(title="Test", date="13-02-2026", purchase_mode=EventPurchaseAccessType.ON_REQUEST)
    )
    result = ParticipantCheckResult(members=["A"], non_members=["B"])
    monkeypatch.setattr("services.events.participants_service.run_basic_checks", lambda *args, **kwargs: result)

    payload = service.check_participants("evt-1", [_checkout_dto()])

    assert payload.members == ["A"]
    assert payload.non_members == ["B"]


def test_check_participants_members_only_rejects_non_members(monkeypatch):
    service = _make_service()
    service.event_repository = _DummyEventRepo(
        model=Event(
            title="Test",
            date="13-02-2026",
            purchase_mode=EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS,
        )
    )
    result = ParticipantCheckResult(non_members=["B"])
    monkeypatch.setattr("services.events.participants_service.run_basic_checks", lambda *args, **kwargs: result)
    with pytest.raises(ValidationError) as exc:
        service.check_participants("evt-1", [_checkout_dto()])
    assert "validation_error" in str(exc.value)


def test_check_participants_happy_path(monkeypatch):
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    monkeypatch.setattr(
        "services.events.participants_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )

    payload = service.check_participants("evt-1", [_checkout_dto()])

    assert payload.valid is True
