import json
from types import SimpleNamespace

import pytest

from dto import CheckoutParticipantDTO, OrderCaptureDTO, PreOrderCartItemDTO, PreOrderDTO
from models import Event, EventOrder, EventPurchaseAccessType, MembershipRef, PurchaseTypes
from services.event_payment_service import EventPaymentService
from services.service_errors import ExternalServiceError, NotFoundError, ValidationError
from domain.participant_rules import ParticipantCheckResult


class _DummyOrdersController:
    def __init__(self, create_response=None, capture_response=None):
        self._create_response = create_response
        self._capture_response = capture_response

    def orders_create(self, payload):
        return self._create_response

    def orders_capture(self, payload):
        return self._capture_response


class _DummyOrderRepo:
    def __init__(self, order_data=None):
        self.saved = []
        self.deleted = []
        self.status_updates = []
        self.order_data = order_data

    def save(self, order_id, order):
        self.saved.append((order_id, order))

    def get(self, order_id):
        return self.order_data

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
    def __init__(self, fee=None):
        self.fee = fee

    def get_price_by_year(self, year):
        return self.fee


class _DummyPurchaseRepo:
    def __init__(self):
        self.created = []
        self.updated = []

    def create(self, purchase):
        self.created.append(purchase)
        return "pur-1"

    def update_participants(self, purchase_id, participants_count, membership_ids):
        self.updated.append((purchase_id, participants_count, membership_ids))


class _DummyMembershipRepo:
    def __init__(self):
        self.appended = []
        self.updated = []
        self.created = []
        self.attended = []
        self.models_by_email = {}

    def find_model_by_email(self, email):
        return self.models_by_email.get(email)

    def update_from_model(self, membership_id, dto):
        self.updated.append((membership_id, dto))

    def append_purchase(self, membership_id, purchase_id):
        self.appended.append((membership_id, purchase_id))

    def create_from_model(self, membership):
        self.created.append(membership)
        return "mem-new"

    def add_attended_event_and_purchase(self, membership_id, event_id, purchase_id):
        self.attended.append((membership_id, event_id, purchase_id))
        return True


class _DummyParticipantRepo:
    def __init__(self):
        self.created = []

    def create(self, event_id, payload):
        self.created.append((event_id, payload))
        return "part-1"


def _make_service():
    service = EventPaymentService.__new__(EventPaymentService)
    service.debug = False
    service.orders_controller = _DummyOrdersController()
    service.event_repository = _DummyEventRepo()
    service.membership_repository = _DummyMembershipRepo()
    service.membership_settings_repository = _DummyMembershipSettingsRepo()
    service.order_repository = _DummyOrderRepo()
    service.purchase_repository = _DummyPurchaseRepo()
    service.participant_repository = _DummyParticipantRepo()
    return service


def _participant(name="Mario"):
    return CheckoutParticipantDTO(
        name=name,
        surname="Rossi",
        email="mario@example.com",
        phone="+390000000000",
        birthdate="01-01-1990",
    )


def _order_payload(order_id="order-1", status="COMPLETED"):
    return {
        "id": order_id,
        "status": status,
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
                            "id": "CAP-1",
                            "status": "COMPLETED",
                            "final_capture": True,
                            "amount": {"value": "10.00", "currency_code": "EUR"},
                            "create_time": "2026-02-13T10:00:00Z",
                            "seller_receivable_breakdown": {
                                "paypal_fee": {"value": "0.5"},
                                "net_amount": {"value": "9.5"},
                            },
                        }
                    ]
                }
            }
        ],
    }


def test_create_order_event_requires_single_cart_item():
    """Rejects payloads with more than one cart item."""
    service = _make_service()
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1"), PreOrderCartItemDTO(eventId="evt-2")])
    with pytest.raises(ValidationError):
        service.create_order_event(payload)


def test_create_order_event_missing_event_or_participants():
    """Rejects missing eventId or empty participants list."""
    service = _make_service()
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="", participants=[])])
    with pytest.raises(ValidationError):
        service.create_order_event(payload)


def test_create_order_event_run_basic_checks_error(monkeypatch):
    """Surfaces validation errors from participant checks."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026")
    service.event_repository = _DummyEventRepo(model=event)

    def fake_checks(*args, **kwargs):
        return ParticipantCheckResult(errors=["err"])

    monkeypatch.setattr("services.event_payment_service.run_basic_checks", fake_checks)
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    with pytest.raises(ValidationError) as exc:
        service.create_order_event(payload)
    assert getattr(exc.value, "details", None) == ["err"]


def test_create_order_event_only_members_requires_fee(monkeypatch):
    """Requires membership fee when new memberships must be created."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026", purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS)
    service.event_repository = _DummyEventRepo(model=event)
    service.membership_settings_repository = _DummyMembershipSettingsRepo(fee=None)

    monkeypatch.setattr(
        "services.event_payment_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    with pytest.raises(ValidationError) as exc:
        service.create_order_event(payload)
    assert "membership fee" in str(exc.value)


def test_create_order_event_only_registered_members_rejects_non_members(monkeypatch):
    """Rejects non-member participants for members-only events."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026", purchase_mode=EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS)
    service.event_repository = _DummyEventRepo(model=event)
    result = ParticipantCheckResult(non_members=["User"])
    monkeypatch.setattr("services.event_payment_service.run_basic_checks", lambda *args, **kwargs: result)
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    with pytest.raises(ValidationError):
        service.create_order_event(payload)


def test_create_order_event_on_request_rejected(monkeypatch):
    """Rejects orders for on-request events."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026", purchase_mode=EventPurchaseAccessType.ON_REQUEST)
    service.event_repository = _DummyEventRepo(model=event)
    monkeypatch.setattr(
        "services.event_payment_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    with pytest.raises(ValidationError):
        service.create_order_event(payload)


def test_create_order_event_paypal_failure(monkeypatch):
    """Fails when PayPal order creation returns non-success status."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026")
    service.event_repository = _DummyEventRepo(model=event)
    service.orders_controller = _DummyOrdersController(create_response=SimpleNamespace(status_code=400, body={}))
    monkeypatch.setattr("services.event_payment_service.ApiHelper.json_serialize", lambda body: json.dumps(body))
    monkeypatch.setattr(
        "services.event_payment_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    with pytest.raises(ExternalServiceError):
        service.create_order_event(payload)


def test_create_order_event_missing_order_id(monkeypatch):
    """Fails when PayPal response lacks an order id."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026")
    service.event_repository = _DummyEventRepo(model=event)
    service.orders_controller = _DummyOrdersController(
        create_response=SimpleNamespace(status_code=201, body={"status": "CREATED"})
    )
    monkeypatch.setattr("services.event_payment_service.ApiHelper.json_serialize", lambda body: json.dumps(body))
    monkeypatch.setattr(
        "services.event_payment_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    with pytest.raises(ExternalServiceError):
        service.create_order_event(payload)


def test_create_order_event_happy_path(monkeypatch):
    """Creates PayPal order and stores staged order successfully."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026", price=10, fee=1)
    service.event_repository = _DummyEventRepo(model=event)
    service.orders_controller = _DummyOrdersController(
        create_response=SimpleNamespace(status_code=201, body={"id": "order-1", "status": "CREATED"})
    )
    monkeypatch.setattr("services.event_payment_service.ApiHelper.json_serialize", lambda body: json.dumps(body))
    monkeypatch.setattr(
        "services.event_payment_service.run_basic_checks",
        lambda *args, **kwargs: ParticipantCheckResult(),
    )
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    result = service.create_order_event(payload)
    assert result["id"] == "order-1"
    assert service.order_repository.saved


def test_create_order_event_only_members_adds_targets(monkeypatch):
    """Stores membership targets for non-member participants in ONLY_MEMBERS events."""
    service = _make_service()
    event = Event(
        title="Test",
        date="13-02-2026",
        price=10,
        fee=1,
        purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
    )
    service.event_repository = _DummyEventRepo(model=event)
    service.membership_settings_repository = _DummyMembershipSettingsRepo(fee=20.0)
    service.orders_controller = _DummyOrdersController(
        create_response=SimpleNamespace(status_code=201, body={"id": "order-2", "status": "CREATED"})
    )

    monkeypatch.setattr("services.event_payment_service.ApiHelper.json_serialize", lambda body: json.dumps(body))

    result = ParticipantCheckResult(
        membership_docs={"mario@example.com": {"id": "mem-1", "email": "mario@example.com"}}
    )
    monkeypatch.setattr("services.event_payment_service.run_basic_checks", lambda *args, **kwargs: result)

    p1 = _participant(name="Mario")
    p2 = CheckoutParticipantDTO(
        name="Luigi",
        surname="Verdi",
        email="luigi@example.com",
        phone="+390000000001",
        birthdate="01-01-1990",
    )
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[p1, p2])])

    response = service.create_order_event(payload)
    assert response["id"] == "order-2"
    saved_order = service.order_repository.saved[0][1]
    assert len(saved_order.membership_targets) == 1
    assert saved_order.membership_fee == 20.0
    assert "mario@example.com" in saved_order.membership_lookup


def test_create_order_event_only_registered_members_success(monkeypatch):
    """Allows ONLY_ALREADY_REGISTERED_MEMBERS when all participants are valid members."""
    service = _make_service()
    event = Event(
        title="Test",
        date="13-02-2026",
        purchase_mode=EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS,
    )
    service.event_repository = _DummyEventRepo(model=event)
    service.orders_controller = _DummyOrdersController(
        create_response=SimpleNamespace(status_code=201, body={"id": "order-3", "status": "CREATED"})
    )

    monkeypatch.setattr("services.event_payment_service.ApiHelper.json_serialize", lambda body: json.dumps(body))
    result = ParticipantCheckResult(
        members=["Mario"],
        non_members=[],
        membership_docs={"mario@example.com": {"id": "mem-1", "email": "mario@example.com"}},
    )
    monkeypatch.setattr("services.event_payment_service.run_basic_checks", lambda *args, **kwargs: result)

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId="evt-1", participants=[_participant()])])
    response = service.create_order_event(payload)
    assert response["id"] == "order-3"
    saved_order = service.order_repository.saved[0][1]
    assert saved_order.membership_lookup.get("mario@example.com")


def test_capture_order_event_missing_order_id():
    """Rejects capture requests without order_id."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.capture_order_event(OrderCaptureDTO(order_id=""))


def test_capture_order_event_updates_status_on_validation_error(monkeypatch):
    """Updates order status if capture validation fails."""
    service = _make_service()
    service.order_repository = _DummyOrderRepo()
    monkeypatch.setattr(service, "capture_paypal_order", lambda order_id: _order_payload(status="FAILED"))

    with pytest.raises(ValidationError):
        service.capture_order_event(OrderCaptureDTO(order_id="order-1"))

    assert service.order_repository.status_updates


def test_capture_order_event_order_not_found(monkeypatch):
    """Raises when the staged order cannot be found."""
    service = _make_service()
    service.order_repository = _DummyOrderRepo(order_data=None)
    monkeypatch.setattr(service, "capture_paypal_order", lambda order_id: _order_payload())
    with pytest.raises(NotFoundError):
        service.capture_order_event(OrderCaptureDTO(order_id="order-1"))


def test_capture_order_event_happy_path(monkeypatch):
    """Captures order, creates purchase, handles memberships, and clears staging."""
    service = _make_service()
    event = Event(title="Test", date="13-02-2026")
    participants = [_participant().to_payload()]
    membership_targets = [_participant(name="Luigi").to_payload()]
    event_order = EventOrder(
        order_id="order-1",
        order_status="CREATED",
        purchase_type=PurchaseTypes.EVENT,
        cart=[{"eventId": "evt-1"}],
        total=10.0,
        reference_id="evt-1",
        event_meta={},
        event_id="evt-1",
        participants=participants,
        event_price=10.0,
        event_fee=1.0,
        membership_targets=membership_targets,
        membership_fee=10.0,
        purchase_mode=EventPurchaseAccessType.PUBLIC,
        membership_lookup={"mario@example.com": {"id": "mem-1", "email": "mario@example.com"}},
    )
    service.order_repository = _DummyOrderRepo(order_data=event_order.to_firestore(include_none=True))
    service.purchase_repository = _DummyPurchaseRepo()
    service.membership_repository = _DummyMembershipRepo()
    service.participant_repository = _DummyParticipantRepo()

    monkeypatch.setattr(service, "capture_paypal_order", lambda order_id: _order_payload())
    monkeypatch.setattr(service, "save_purchase", lambda *args, **kwargs: "pur-1")
    monkeypatch.setattr(
        service,
        "create_memberships_for_targets",
        lambda *args, **kwargs: [MembershipRef(email="new@example.com", membership_id="mem-2")],
    )
    handled = {}
    monkeypatch.setattr(
        service,
        "handle_event_participants",
        lambda *args, **kwargs: handled.update({"called": True}),
    )

    result = service.capture_order_event(OrderCaptureDTO(order_id="order-1"))

    assert result["purchase_id"] == "pur-1"
    assert handled.get("called") is True
    assert service.purchase_repository.updated
    assert service.order_repository.deleted == ["order-1"]
