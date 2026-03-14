from io import BytesIO
from types import SimpleNamespace

import pytest

from dto import MembershipDTO, EventDTO
from models import Membership, Purchase, Event
from services.memberships.memberships_service import MembershipsService
from errors.service_errors import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


class _DummyMembershipRepo:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.models = {}
        self.by_slug = {}
        self.by_email = {}
        self.by_phone = {}
        self._all = []

    def get_all(self):
        return self._all

    def get_model(self, membership_id):
        return self.models.get(membership_id)

    def get_model_by_slug(self, slug):
        return self.by_slug.get(slug)

    def create_from_model(self, membership):
        membership_id = "mem-1"
        self.created.append(membership)
        self.models[membership_id] = membership
        return membership_id

    def update_from_model(self, membership_id, payload):
        self.updated.append((membership_id, payload))
        return True

    def delete(self, membership_id):
        self.deleted.append(membership_id)
        self.models.pop(membership_id, None)

    def find_by_email(self, email):
        if email in self.by_email:
            return self.by_email[email]
        return None

    def find_by_phone(self, phone):
        if phone in self.by_phone:
            return self.by_phone[phone]
        return None


class _DummySettingsRepo:
    def __init__(self):
        self.prices = {}

    def set_price_by_year(self, year, price):
        self.prices[year] = price

    def get_price_by_year(self, year):
        return self.prices.get(year)


class _DummyParticipantRepo:
    def __init__(self, removed=0):
        self.removed = removed

    def clear_membership_reference(self, membership_id):
        return self.removed


class _DummyPurchaseRepo:
    def __init__(self, models=None):
        self.models = models or {}

    def get_model(self, purchase_id):
        return self.models.get(purchase_id)


class _DummyEventRepo:
    def __init__(self, models=None):
        self.models = models or {}

    def get_model(self, event_id):
        return self.models.get(event_id)


class _DummyBlob:
    def __init__(self, exists=True, data=b"pdf-data"):
        self._exists = exists
        self.deleted = False
        self._data = data
        self.public_url = "https://example.com/memberships/cards/mem-1.pdf"

    def exists(self):
        return self._exists

    def delete(self):
        self.deleted = True

    def download_as_bytes(self):
        return self._data


class _DummyStorage:
    def __init__(self, blob=None):
        self._blob = blob or _DummyBlob()
        self.last_path = None

    def blob(self, path):
        self.last_path = path
        return self._blob


class _DummyDocumentsService:
    def __init__(self, doc=None, storage=None, should_fail=False):
        self.storage = storage or _DummyStorage()
        self._doc = doc or SimpleNamespace(
            public_url="https://example.com/memberships/cards/mem-1.pdf",
            storage_path="memberships/cards/mem-1.pdf",
            buffer=BytesIO(b"pdf"),
        )
        self._should_fail = should_fail
        self.calls = []

    def create_membership_card(self, membership_id, membership_data):
        self.calls.append((membership_id, membership_data))
        if self._should_fail:
            raise RuntimeError("boom")
        return self._doc


def _make_service():
    service = MembershipsService()
    service.membership_repository = _DummyMembershipRepo()
    service.settings_repository = _DummySettingsRepo()
    service.participant_repository = _DummyParticipantRepo()
    service.purchase_repository = _DummyPurchaseRepo()
    service.event_repository = _DummyEventRepo()
    service.documents_service = _DummyDocumentsService()
    return service


def test_get_by_id_not_found():
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.get_by_id("missing")


def test_get_by_id_slug_success():
    service = _make_service()
    membership = Membership(name="Mario")
    membership.id = "mem-1"
    service.membership_repository.by_slug["slug-1"] = membership
    payload = service.get_by_id(None, slug="slug-1")
    assert payload["id"] == "mem-1"
    assert payload["name"] == "Mario"


def test_create_rejects_protected_fields():
    service = _make_service()
    dto = MembershipDTO(slug="slug")
    with pytest.raises(ForbiddenError):
        service.create(dto)


def test_create_rejects_minor():
    service = _make_service()
    dto = MembershipDTO(birthdate="01-01-2015", email="test@example.com")
    with pytest.raises(ValidationError):
        service.create(dto)


def test_create_requires_contact():
    service = _make_service()
    dto = MembershipDTO(birthdate="01-01-1990")
    with pytest.raises(ValidationError):
        service.create(dto)


def test_create_conflict_email():
    service = _make_service()
    service.membership_repository.by_email["test@example.com"] = ("mem-x", {})
    dto = MembershipDTO(birthdate="01-01-1990", email="test@example.com")
    with pytest.raises(ConflictError):
        service.create(dto)


def test_create_happy_path():
    service = _make_service()
    dto = MembershipDTO(
        name="Mario",
        surname="Rossi",
        birthdate="01-01-1990",
        email=" Mario@Example.Com ",
        phone=" +39 000 000 ",
        membership_fee=10,
    )

    payload = service.create(dto)

    created = service.membership_repository.created[0]
    assert payload["id"] == "mem-1"
    assert created.email == "mario@example.com"
    assert created.phone == "+39000000"
    assert created.subscription_valid is True
    assert created.membership_sent is False
    assert created.start_date is not None
    assert created.end_date is not None


def test_update_rejects_protected_fields():
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(birthdate="01-01-1990")
    dto = MembershipDTO(card_url="x")
    with pytest.raises(ForbiddenError):
        service.update("mem-1", dto)


def test_update_not_found():
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.update("missing", MembershipDTO())


def test_update_rejects_minor():
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(birthdate="01-01-1990")
    dto = MembershipDTO(birthdate="01-01-2015", email="test@example.com")
    with pytest.raises(ValidationError):
        service.update("mem-1", dto)


def test_update_requires_contact():
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(birthdate="01-01-1990")
    dto = MembershipDTO()
    with pytest.raises(ValidationError):
        service.update("mem-1", dto)


def test_update_conflict_email():
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(birthdate="01-01-1990", email="old@example.com")
    service.membership_repository.by_email["new@example.com"] = ("mem-2", {})
    dto = MembershipDTO(email="new@example.com")
    with pytest.raises(ConflictError):
        service.update("mem-1", dto)


def test_update_email_change_does_not_regenerate_card():
    service = _make_service()
    service.documents_service = _DummyDocumentsService()
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="old@example.com",
        card_url="https://example.com/memberships/cards/mem-1.pdf",
        card_storage_path="memberships/cards/mem-1.pdf",
    )
    dto = MembershipDTO(email="new@example.com")

    payload = service.update("mem-1", dto)

    assert payload["message"] == "Membership aggiornata"
    assert service.documents_service.calls == []
    assert service.membership_repository.updated


def test_update_email_change_ignores_card_generation_failures():
    service = _make_service()
    service.documents_service = _DummyDocumentsService(should_fail=True)
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="old@example.com",
    )
    dto = MembershipDTO(email="new@example.com")
    payload = service.update("mem-1", dto)
    assert payload["message"] == "Membership aggiornata"
    assert service.documents_service.calls == []
    assert service.membership_repository.updated


def test_delete_removes_card_and_membership():
    service = _make_service()
    blob = _DummyBlob()
    storage = _DummyStorage(blob=blob)
    service.documents_service = _DummyDocumentsService(storage=storage)
    service.participant_repository = _DummyParticipantRepo(removed=2)
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        card_storage_path="memberships/cards/mem-1.pdf",
    )

    payload = service.delete("mem-1")

    assert payload["message"]
    assert blob.deleted is True
    assert "mem-1" in service.membership_repository.deleted


def test_send_card_does_not_require_card_url_format(monkeypatch):
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="test@example.com",
        name="Mario",
        surname="Rossi",
        card_url="https://example.com/invalid.pdf",
    )
    monkeypatch.setattr("services.memberships.memberships_service.mail_service.send", lambda *args, **kwargs: True)
    payload = service.send_card("mem-1")
    assert payload["message"] == "Card sent successfully"


def test_send_card_email_failure(monkeypatch):
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="test@example.com",
        name="Mario",
        surname="Rossi",
        end_date="2026-12-31",
        card_url="https://example.com/memberships/cards/mem-1.pdf",
        card_storage_path="memberships/cards/mem-1.pdf",
    )
    monkeypatch.setattr("services.memberships.memberships_service.mail_service.send", lambda *args, **kwargs: False)
    with pytest.raises(ExternalServiceError):
        service.send_card("mem-1")


def test_send_card_happy_path(monkeypatch):
    service = _make_service()
    blob = _DummyBlob()
    service.documents_service = _DummyDocumentsService(storage=_DummyStorage(blob=blob))
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="test@example.com",
        name="Mario",
        surname="Rossi",
        end_date="2026-12-31",
        card_url="https://example.com/memberships/cards/mem-1.pdf",
        card_storage_path="memberships/cards/mem-1.pdf",
    )

    monkeypatch.setattr("services.memberships.memberships_service.mail_service.send", lambda *args, **kwargs: True)
    payload = service.send_card("mem-1")

    assert payload["message"] == "Card sent successfully"
    assert service.membership_repository.updated


def test_get_purchases_happy_path():
    service = _make_service()
    purchase = Purchase(payer_name="A", payer_surname="B")
    purchase.id = "pur-1"
    service.purchase_repository = _DummyPurchaseRepo(models={"pur-1": purchase})
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        purchases=["pur-1"],
    )

    payload = service.get_purchases("mem-1")

    assert payload[0]["id"] == "pur-1"
    assert payload[0]["payer_name"] == "A"


def test_get_events_happy_path():
    service = _make_service()
    event = Event(title="Test", date="13-02-2026")
    event.id = "evt-1"
    service.event_repository = _DummyEventRepo(models={"evt-1": event})
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        attended_events=["evt-1"],
    )

    payload = service.get_events("mem-1")

    assert payload == [EventDTO.from_model(event).membership_event_payload()]


def test_membership_price_roundtrip():
    service = _make_service()
    payload = service.set_membership_price(20, year=2026)
    assert payload["message"]

    result = service.get_membership_price(year=2026)
    assert result == {"year": "2026", "price": 20}


def test_membership_price_not_found():
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.get_membership_price(year=2026)
