from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest

from dto.membership_api import CreateMembershipRequestDTO, RenewMembershipRequestDTO, UpdateMembershipRequestDTO
from errors.service_errors import ConflictError, ExternalServiceError, NotFoundError, ValidationError
from models import Event, Membership, MembershipPassResult, Purchase, PurchaseTypes
from services.memberships.memberships_service import MembershipsService
from services.memberships.renewal_command import RenewMembershipCommand


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

    def list(self):
        return self._all

    def find_by_year(self, year):
        return [m for m in self._all if year in (m.membership_years or [])]

    def get(self, membership_id):
        return self.models.get(membership_id)

    def get_model_by_slug(self, slug):
        return self.by_slug.get(slug)

    def create_from_model(self, membership):
        membership_id = "mem-1"
        membership.id = membership_id
        self.created.append(membership)
        self.models[membership_id] = membership
        return membership_id

    def update_from_model(self, membership_id, membership):
        membership.id = membership_id
        self.models[membership_id] = membership
        self.updated.append((membership_id, membership))
        return True

    def delete(self, membership_id):
        self.deleted.append(membership_id)
        self.models.pop(membership_id, None)

    def find_by_email(self, email):
        return self.by_email.get(email)

    def find_by_phone(self, phone):
        return self.by_phone.get(phone)


class _DummySettingsRepo:
    def __init__(self):
        self.prices = {}
        self.wallet_model = None

    def set_price_by_year(self, year, price):
        self.prices[year] = price

    def get_price_by_year(self, year):
        return self.prices.get(year)

    def get_wallet_model(self):
        return self.wallet_model

    def set_wallet_model(self, model_id):
        self.wallet_model = model_id


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
    def __init__(self, storage=None):
        self.storage = storage or _DummyStorage()
        self.calls = []

    def create_membership_card(self, membership_id, membership_data):
        self.calls.append((membership_id, membership_data))
        return SimpleNamespace(
            public_url=f"https://example.com/{membership_id}.pdf",
            storage_path=f"memberships/cards/{membership_id}.pdf",
            buffer=BytesIO(b"pdf"),
        )


class _DummyPass2UService:
    def __init__(self, wallet=None, invalidate_ok=True):
        self.wallet = wallet
        self.invalidate_ok = invalidate_ok
        self.created_for = []
        self.invalidated = []

    def create_membership_pass(self, membership_id, membership):
        self.created_for.append((membership_id, membership))
        return self.wallet

    def invalidate_membership_pass(self, pass_id):
        self.invalidated.append(pass_id)
        return self.invalidate_ok


class _DummyMailService:
    def __init__(self, sent=True):
        self.sent = sent
        self.messages = []

    def send(self, message):
        self.messages.append(message)
        return self.sent


def _make_service(pass2u=None, mail=None):
    return MembershipsService(
        membership_repository=_DummyMembershipRepo(),
        settings_repository=_DummySettingsRepo(),
        purchase_repository=_DummyPurchaseRepo(),
        participant_repository=_DummyParticipantRepo(),
        event_repository=_DummyEventRepo(),
        documents_service=_DummyDocumentsService(),
        pass2u_service=pass2u or _DummyPass2UService(),
        mail_service_instance=mail or _DummyMailService(),
    )


def _create_dto(**overrides):
    payload = {
        "name": "Mario",
        "surname": "Rossi",
        "birthdate": "01-01-1990",
        "email": " Mario@Example.Com ",
        "phone": " +39 000 000 ",
        "membership_fee": 10,
    }
    payload.update(overrides)
    return CreateMembershipRequestDTO.model_validate(payload)


def _update_dto(**overrides):
    payload = {"membership_id": "mem-1"}
    payload.update(overrides)
    return UpdateMembershipRequestDTO.model_validate(payload)


def _previous_year_member(**overrides):
    prev_year = datetime.now(timezone.utc).year - 1
    defaults = {
        "name": "Mario",
        "surname": "Rossi",
        "email": "mario@example.com",
        "phone": "+39333000001",
        "birthdate": "01-01-1990",
        "start_date": f"{prev_year}-06-01T10:00:00+00:00",
        "end_date": f"31-12-{prev_year}",
        "subscription_valid": True,
        "membership_sent": True,
        "membership_type": "manual",
        "wallet_pass_id": "old-pass-id",
        "wallet_url": "https://wallet.example/old",
        "membership_years": [prev_year],
    }
    defaults.update(overrides)
    member = Membership(**defaults)
    member.id = "mem-prev"
    return member


def _renew_command(**overrides):
    curr_year = datetime.now(timezone.utc).year
    defaults = {
        "membership_id": "mem-prev",
        "start_date": f"{curr_year}-03-19T10:00:00+00:00",
        "end_date": f"31-12-{curr_year}",
        "purchase_id": "pur-renew",
        "fee": 20.0,
        "membership_type": "event",
        "send_card": False,
        "invalidate_wallet": True,
        "create_wallet": False,
    }
    defaults.update(overrides)
    return RenewMembershipCommand(**defaults)


def test_get_by_id_slug_success():
    service = _make_service()
    membership = Membership(name="Mario")
    membership.id = "mem-1"
    service.membership_repository.by_slug["slug-1"] = membership

    response = service.get_by_id(None, slug="slug-1")

    assert response.id == "mem-1"
    assert response.name == "Mario"


def test_get_by_id_not_found():
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.get_by_id("missing")


def test_create_rejects_minor():
    service = _make_service()
    dto = _create_dto(birthdate="01-01-2015")

    with pytest.raises(ValidationError):
        service.create(dto)


def test_create_requires_contact():
    service = _make_service()
    dto = _create_dto(email=None, phone=None)

    with pytest.raises(ValidationError):
        service.create(dto)


def test_create_conflict_email_for_current_membership():
    service = _make_service()
    current_year = datetime.now(timezone.utc).year
    conflict = Membership(
        email="mario@example.com",
        birthdate="01-01-1990",
        start_date=f"{current_year}-01-01T00:00:00+00:00",
        end_date=f"31-12-{current_year}",
        membership_years=[current_year],
    )
    conflict.id = "mem-existing"
    service.membership_repository.by_email["mario@example.com"] = conflict

    with pytest.raises(ConflictError):
        service.create(_create_dto(email="mario@example.com"))


def test_create_happy_path_builds_membership_model():
    service = _make_service()

    response = service.create(_create_dto())

    created = service.membership_repository.created[0]
    assert response.id == "mem-1"
    assert created.email == "mario@example.com"
    assert created.phone == "+39000000"
    assert created.subscription_valid is True
    assert created.membership_sent is False
    assert created.start_date is not None
    assert created.end_date is not None
    assert created.renewals
    assert created.membership_years


def test_create_triggers_renewal_for_previous_year_member():
    service = _make_service()
    member = _previous_year_member()
    service.membership_repository.models[member.id] = member
    service.membership_repository.by_email[member.email] = member

    response = service.create(
        _create_dto(email=member.email, phone=member.phone, send_card_on_create=False)
    )

    updated = service.membership_repository.models[member.id]
    assert response.renewed is True
    assert updated.membership_sent is False
    assert updated.subscription_valid is True
    assert updated.wallet_pass_id is None
    assert updated.wallet_url is None
    assert datetime.now(timezone.utc).year in updated.membership_years


def test_renew_creates_new_wallet_when_provider_returns_one():
    wallet = MembershipPassResult(
        pass_id="new-pass",
        wallet_url="https://wallet.example/new",
        apple_wallet_url="https://wallet.example/new",
        google_wallet_url="https://wallet.example/new",
    )
    pass2u = _DummyPass2UService(wallet=wallet)
    service = _make_service(pass2u=pass2u)
    member = _previous_year_member()
    service.membership_repository.models[member.id] = member

    response = service.renew(
        member.id,
        RenewMembershipRequestDTO.model_validate({"membership_id": member.id}),
    )

    renewed = service.membership_repository.models[member.id]
    assert response.renewed is True
    assert pass2u.invalidated == ["old-pass-id"]
    assert renewed.wallet_pass_id == "new-pass"
    assert renewed.wallet_url == "https://wallet.example/new"


def test_renew_existing_updates_history_years_purchase_and_current_state():
    service = _make_service()
    prev_year = datetime.now(timezone.utc).year - 1
    curr_year = datetime.now(timezone.utc).year
    member = _previous_year_member(
        renewals=[
            {
                "year": prev_year,
                "start_date": f"{prev_year}-06-01T10:00:00+00:00",
                "end_date": f"31-12-{prev_year}",
                "purchase_id": "pur-old",
                "fee": 10.0,
            }
        ],
        purchases=["pur-old"],
    )

    renewed = service.renew_existing(member, _renew_command())

    assert renewed.start_date == f"{curr_year}-03-19T10:00:00+00:00"
    assert renewed.end_date == f"31-12-{curr_year}"
    assert renewed.subscription_valid is True
    assert renewed.membership_sent is False
    assert renewed.membership_type == "event"
    assert renewed.membership_fee == 20.0
    assert renewed.wallet_pass_id is None
    assert renewed.wallet_url is None
    assert renewed.purchases == ["pur-old", "pur-renew"]
    assert renewed.membership_years == [prev_year, curr_year]
    assert renewed.renewals[-1] == {
        "year": curr_year,
        "start_date": f"{curr_year}-03-19T10:00:00+00:00",
        "end_date": f"31-12-{curr_year}",
        "purchase_id": "pur-renew",
        "fee": 20.0,
    }
    assert service.membership_repository.models[member.id] is renewed


def test_renew_existing_invalidates_old_wallet_without_creating_new_one():
    pass2u = _DummyPass2UService()
    service = _make_service(pass2u=pass2u)
    member = _previous_year_member(wallet_pass_id="old-pass", wallet_url="https://wallet.example/old")

    renewed = service.renew_existing(member, _renew_command(create_wallet=False))

    assert pass2u.invalidated == ["old-pass"]
    assert pass2u.created_for == []
    assert renewed.wallet_pass_id is None
    assert renewed.wallet_url is None


def test_renew_existing_can_keep_existing_wallet_when_invalidation_disabled():
    pass2u = _DummyPass2UService()
    service = _make_service(pass2u=pass2u)
    member = _previous_year_member(wallet_pass_id="old-pass", wallet_url="https://wallet.example/old")

    renewed = service.renew_existing(
        member,
        _renew_command(invalidate_wallet=False, create_wallet=False),
    )

    assert pass2u.invalidated == []
    assert pass2u.created_for == []
    assert renewed.wallet_pass_id == "old-pass"
    assert renewed.wallet_url == "https://wallet.example/old"


def test_renew_existing_creates_new_wallet_when_requested():
    wallet = MembershipPassResult(
        pass_id="new-pass",
        wallet_url="https://wallet.example/new",
        apple_wallet_url="https://wallet.example/new",
        google_wallet_url="https://wallet.example/new",
    )
    pass2u = _DummyPass2UService(wallet=wallet)
    service = _make_service(pass2u=pass2u)
    member = _previous_year_member(wallet_pass_id="old-pass", wallet_url="https://wallet.example/old")

    renewed = service.renew_existing(member, _renew_command(create_wallet=True))

    assert pass2u.invalidated == ["old-pass"]
    assert pass2u.created_for
    assert renewed.wallet_pass_id == "new-pass"
    assert renewed.wallet_url == "https://wallet.example/new"


def test_renew_existing_send_card_is_non_blocking(monkeypatch):
    service = _make_service()
    member = _previous_year_member()
    calls = []

    def failing_send_card(membership_id):
        calls.append(membership_id)
        raise ExternalServiceError("mail down")

    monkeypatch.setattr(service, "send_card", failing_send_card)

    renewed = service.renew_existing(member, _renew_command(send_card=True))

    assert calls == [member.id]
    assert renewed.subscription_valid is True
    assert renewed.membership_sent is False


def test_update_conflict_email_marks_mergeable():
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="old@example.com",
    )
    conflict = Membership(name="Luigi", surname="Verdi", email="new@example.com", birthdate="01-01-1990")
    conflict.id = "mem-2"
    service.membership_repository.by_email["new@example.com"] = conflict

    with pytest.raises(ConflictError) as exc:
        service.update("mem-1", _update_dto(email="new@example.com"))

    assert exc.value.payload["mergeable"] is True
    assert exc.value.payload["conflicting_id"] == "mem-2"


def test_update_happy_path_persists_model():
    service = _make_service()
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="old@example.com",
        phone="+3900001",
    )

    response = service.update("mem-1", _update_dto(email="new@example.com"))

    updated = service.membership_repository.models["mem-1"]
    assert response.message == "Membership aggiornata"
    assert updated.email == "new@example.com"


def test_delete_invalidates_wallet_and_removes_card():
    pass2u = _DummyPass2UService()
    service = _make_service(pass2u=pass2u)
    blob = _DummyBlob()
    service.documents_service = _DummyDocumentsService(storage=_DummyStorage(blob=blob))
    service.participant_repository = _DummyParticipantRepo(removed=2)
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        wallet_pass_id="pass-old",
        card_storage_path="memberships/cards/mem-1.pdf",
    )

    response = service.delete("mem-1")

    assert response.id == "mem-1"
    assert blob.deleted is True
    assert pass2u.invalidated == ["pass-old"]
    assert "mem-1" in service.membership_repository.deleted


def test_send_card_generates_wallet_and_marks_sent():
    wallet = MembershipPassResult(
        pass_id="pass-1",
        wallet_url="https://wallet.example/pass-1",
        apple_wallet_url="https://wallet.example/pass-1",
        google_wallet_url="https://wallet.example/pass-1",
    )
    mail = _DummyMailService(sent=True)
    service = _make_service(pass2u=_DummyPass2UService(wallet=wallet), mail=mail)
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="test@example.com",
        name="Mario",
        surname="Rossi",
        end_date="31-12-2026",
    )

    response = service.send_card("mem-1")

    membership = service.membership_repository.models["mem-1"]
    assert response.message == "Card sent successfully"
    assert membership.membership_sent is True
    assert membership.wallet_pass_id == "pass-1"
    assert len(mail.messages) == 1


def test_send_card_email_failure_raises_external_error():
    service = _make_service(mail=_DummyMailService(sent=False))
    service.membership_repository.models["mem-1"] = Membership(
        birthdate="01-01-1990",
        email="test@example.com",
        name="Mario",
        surname="Rossi",
        end_date="31-12-2026",
        wallet_url="https://wallet.example/existing",
    )

    with pytest.raises(ExternalServiceError):
        service.send_card("mem-1")


def test_get_purchases_returns_response_payloads():
    service = _make_service()
    purchase = Purchase(
        payer_name="A",
        payer_surname="B",
        purchase_type=PurchaseTypes.EVENT,
    )
    purchase.id = "pur-1"
    service.purchase_repository = _DummyPurchaseRepo(models={"pur-1": purchase})
    service.membership_repository.models["mem-1"] = Membership(purchases=["pur-1"])

    payload = service.get_purchases("mem-1")

    assert payload[0]["id"] == "pur-1"
    assert payload[0]["payer_name"] == "A"


def test_get_events_returns_minimal_event_payloads():
    service = _make_service()
    event = Event(title="Test", date="13-02-2026")
    event.id = "evt-1"
    service.event_repository = _DummyEventRepo(models={"evt-1": event})
    service.membership_repository.models["mem-1"] = Membership(attended_events=["evt-1"])

    payload = service.get_events("mem-1")

    assert payload == [{"id": "evt-1", "title": "Test", "date": "13-02-2026", "image": None}]


def test_membership_price_roundtrip():
    service = _make_service()

    response = service.set_membership_price(20, year=2026)
    result = service.get_membership_price(year=2026)

    assert response.price == 20
    assert result.year == "2026"
    assert result.price == 20


def test_wallet_model_roundtrip():
    service = _make_service()

    service.set_wallet_model("model-1")
    response = service.get_wallet_model()

    assert response.model_id == "model-1"
