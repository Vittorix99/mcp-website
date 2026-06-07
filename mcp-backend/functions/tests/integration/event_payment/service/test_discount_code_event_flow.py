import json
import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from config.firebase_config import db
from dto.discount_code_dto import CreateDiscountCodeRequestDTO, UpdateDiscountCodeRequestDTO
from dto.preorder import CheckoutParticipantDTO, OrderCaptureDTO, PreOrderCartItemDTO, PreOrderDTO
from errors.service_errors import ConflictError, ValidationError
from models import EventOrder, EventPurchaseAccessType, Membership, PurchaseTypes
from repositories.discount_code_repository import DiscountCodeRepository
from repositories.membership_repository import MembershipRepository
from repositories.order_repository import OrderRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.payments.discount_code_admin_service import DiscountCodeAdminService
from services.payments.discount_code_service import DiscountCodeService
from services.payments.event_payment_service import EventPaymentService


@pytest.fixture(autouse=True)
def _require_firestore_emulator():
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.skip("Firestore emulator non attivo — FIRESTORE_EMULATOR_HOST non impostato")
    if not getattr(db, "_emulator_host", None):
        pytest.skip("Firestore client non configurato sull'emulatore")


class _FakeOrdersController:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.create_payload = None

    def orders_create(self, payload):
        self.create_payload = payload
        return SimpleNamespace(
            status_code=201,
            body={
                "id": self.order_id,
                "status": "CREATED",
                "links": [],
            },
        )


class _FakePayPalClient:
    def __init__(self, order_id: str):
        self.orders = _FakeOrdersController(order_id)


@pytest.fixture
def discount_repo():
    return DiscountCodeRepository()


@pytest.fixture
def membership_repo():
    return MembershipRepository()


@pytest.fixture
def order_repo():
    return OrderRepository()


@pytest.fixture
def purchase_repo():
    return PurchaseRepository()


@pytest.fixture
def participant_repo():
    return ParticipantRepository()


@pytest.fixture
def discount_admin_service(discount_repo):
    return DiscountCodeAdminService(discount_code_repository=discount_repo)


@pytest.fixture
def discount_service(discount_repo, membership_repo):
    return DiscountCodeService(
        discount_code_repository=discount_repo,
        membership_repository=membership_repo,
    )


@pytest.fixture
def created_discounts():
    ids = []
    yield ids
    for discount_id in ids:
        try:
            db.collection("discount_codes").document(discount_id).delete()
        except Exception:
            pass


def _create_discount(
    service: DiscountCodeAdminService,
    created_ids: list[str],
    event_id: str,
    *,
    code: str,
    discount_type: str = "PERCENTAGE",
    discount_value: float = 50.0,
    max_uses: int = 5,
    restricted_membership_id: str | None = None,
    restricted_email: str | None = None,
):
    dto = CreateDiscountCodeRequestDTO.model_validate(
        {
            "code": code,
            "discountType": discount_type,
            "discountValue": discount_value,
            "maxUses": max_uses,
            "restrictedMembershipId": restricted_membership_id,
            "restrictedEmail": restricted_email,
        }
    )
    response = service.create_discount_code(event_id, dto, admin_uid="admin-test")
    created_ids.append(response.id)
    return response


def _participant(email: str, *, name: str = "Mario", surname: str = "Rossi") -> CheckoutParticipantDTO:
    return CheckoutParticipantDTO(
        name=name,
        surname=surname,
        email=email,
        phone="+390000000000",
        birthdate="01-01-1990",
    )


def _preorder(event_id: str, participants: list[CheckoutParticipantDTO], discount_code: str | None = None) -> PreOrderDTO:
    return PreOrderDTO(
        cart=[
            PreOrderCartItemDTO(
                eventId=event_id,
                participants=participants,
                discountCode=discount_code,
            )
        ]
    )


def _capture_payload(order_id: str, event_id: str, amount: float, payer_email: str) -> dict:
    return {
        "id": order_id,
        "status": "COMPLETED",
        "payment_source": {
            "paypal": {
                "name": {"given_name": "Mario", "surname": "Rossi"},
                "email_address": payer_email,
            }
        },
        "purchase_units": [
            {
                "reference_id": event_id,
                "payments": {
                    "captures": [
                        {
                            "id": f"CAP-{uuid4().hex[:8]}",
                            "status": "COMPLETED",
                            "final_capture": True,
                            "amount": {"value": f"{amount:.2f}", "currency_code": "EUR"},
                            "create_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                            "seller_receivable_breakdown": {
                                "paypal_fee": {"value": "0.50"},
                                "net_amount": {"value": f"{max(amount - 0.50, 0):.2f}"},
                            },
                        }
                    ]
                },
            }
        ],
    }


def _event_participants_collection(event_id: str):
    return db.collection("participants").document(event_id).collection("participants_event")


def _cleanup_event_flow(event_id: str, order_id: str | None = None, purchase_id: str | None = None):
    for snap in _event_participants_collection(event_id).stream():
        snap.reference.delete()
    if purchase_id:
        db.collection("purchases").document(purchase_id).delete()
    for snap in db.collection("purchases").where("event_id", "==", event_id).stream():
        snap.reference.delete()
    if order_id:
        db.collection("orders").document(order_id).delete()


@pytest.mark.integration
def test_discount_code_admin_crud_uniqueness_and_soft_delete(
    create_event,
    discount_admin_service,
    discount_repo,
    created_discounts,
):
    event_id = create_event(price=20.0, fee=1.0)

    created = _create_discount(
        discount_admin_service,
        created_discounts,
        event_id,
        code=" mcp50 ",
        discount_type="PERCENTAGE",
        discount_value=50,
        max_uses=3,
    )

    assert created.code == "MCP50"
    assert created.used_count == 0
    assert created.is_active is True

    by_code = discount_repo.get_by_code_and_event("mcp50", event_id)
    assert by_code is not None
    assert by_code.id == created.id
    assert by_code.code == "MCP50"

    listed = discount_admin_service.list_discount_codes(event_id)
    assert [item.id for item in listed] == [created.id]

    with pytest.raises(ConflictError):
        _create_discount(
            discount_admin_service,
            created_discounts,
            event_id,
            code="MCP50",
            discount_type="PERCENTAGE",
            discount_value=25,
            max_uses=1,
        )

    updated = discount_admin_service.update_discount_code(
        created.id,
        UpdateDiscountCodeRequestDTO.model_validate({"maxUses": 5, "discountValue": 40}),
        admin_uid="admin-test",
    )
    assert updated.max_uses == 5
    assert updated.discount_value == 40

    disabled = discount_admin_service.disable_discount_code(created.id, admin_uid="admin-test")
    assert disabled.is_active is False


@pytest.mark.integration
def test_validate_discount_code_use_cases_against_firestore(
    create_event,
    discount_admin_service,
    discount_service,
    membership_repo,
    created_discounts,
):
    event_id = create_event(price=25.0, fee=1.0)
    member = Membership(
        name="Giulia",
        surname="Verdi",
        email="member-discount@example.com",
        phone="+390000000001",
        birthdate="01-01-1990",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=f"31-12-{datetime.now(timezone.utc).year}",
        subscription_valid=True,
    )
    membership_id = membership_repo.create_from_model(member)

    try:
        valid = _create_discount(
            discount_admin_service,
            created_discounts,
            event_id,
            code="fixedprice",
            discount_type="FIXED_PRICE",
            discount_value=10,
            max_uses=2,
        )
        inactive = _create_discount(
            discount_admin_service,
            created_discounts,
            event_id,
            code="off",
            discount_type="FIXED",
            discount_value=5,
            max_uses=2,
        )
        discount_admin_service.disable_discount_code(inactive.id, admin_uid="admin-test")
        exhausted = _create_discount(
            discount_admin_service,
            created_discounts,
            event_id,
            code="done",
            discount_type="FIXED",
            discount_value=5,
            max_uses=1,
        )
        db.collection("discount_codes").document(exhausted.id).update({"usedCount": 1})
        email_restricted = _create_discount(
            discount_admin_service,
            created_discounts,
            event_id,
            code="emailonly",
            discount_type="PERCENTAGE",
            discount_value=20,
            max_uses=2,
            restricted_email="allowed@example.com",
        )
        membership_restricted = _create_discount(
            discount_admin_service,
            created_discounts,
            event_id,
            code="memberonly",
            discount_type="FIXED",
            discount_value=5,
            max_uses=2,
            restricted_membership_id=membership_id,
        )

        assert discount_service.validate_discount_code(
            event_id=event_id,
            code="missing",
            participants_count=1,
            payer_email="buyer@example.com",
            event_price=25,
        ).error_message == "Codice sconto non valido"
        assert discount_service.validate_discount_code(
            event_id=event_id,
            code=inactive.code,
            participants_count=1,
            payer_email="buyer@example.com",
            event_price=25,
        ).error_message == "Codice sconto non più disponibile"
        assert discount_service.validate_discount_code(
            event_id=event_id,
            code=exhausted.code,
            participants_count=1,
            payer_email="buyer@example.com",
            event_price=25,
        ).error_message == "Codice sconto non più disponibile"
        assert discount_service.validate_discount_code(
            event_id=event_id,
            code=valid.code,
            participants_count=2,
            payer_email="buyer@example.com",
            event_price=25,
        ).error_message == "Il codice sconto è valido solo per acquisti singoli"
        assert discount_service.validate_discount_code(
            event_id=event_id,
            code=email_restricted.code,
            participants_count=1,
            payer_email="denied@example.com",
            event_price=25,
        ).error_message == "Codice sconto non disponibile per questa email"
        assert discount_service.validate_discount_code(
            event_id=event_id,
            code=membership_restricted.code,
            participants_count=1,
            payer_email="other@example.com",
            payer_membership_id=membership_id,
            event_price=25,
        ).error_message == "Codice sconto non disponibile per questo account"

        success = discount_service.validate_discount_code(
            event_id=event_id,
            code=" fixedprice ",
            participants_count=1,
            payer_email="buyer@example.com",
            event_price=25,
        )
        assert success.valid is True
        assert success.discount_code_id == valid.id
        assert success.discount_type == "FIXED_PRICE"
        assert success.final_price == 10.0
        assert success.discount_amount == 15.0

        membership_success = discount_service.validate_discount_code(
            event_id=event_id,
            code=membership_restricted.code,
            participants_count=1,
            payer_email="member-discount@example.com",
            payer_membership_id=membership_id,
            event_price=25,
        )
        assert membership_success.valid is True
    finally:
        membership_repo.delete(membership_id)


@pytest.mark.integration
def test_create_order_event_with_discount_stores_staging_order_fields(
    create_event,
    discount_admin_service,
    order_repo,
    created_discounts,
):
    event_id = create_event(price=25.0, fee=1.5)
    discount = _create_discount(
        discount_admin_service,
        created_discounts,
        event_id,
        code="mcp50",
        discount_type="PERCENTAGE",
        discount_value=50,
        max_uses=5,
    )
    order_id = f"ORDER-DISCOUNT-{uuid4().hex[:8]}"
    fake_paypal = _FakePayPalClient(order_id)
    service = EventPaymentService(paypal_client=fake_paypal)

    try:
        with patch("services.payments.event_payment_service.ApiHelper.json_serialize", side_effect=lambda body: json.dumps(body)):
            result = service.create_order_event(
                _preorder(event_id, [_participant("buyer-create@example.com")], discount_code="mcp50")
            )

        assert result.id == order_id
        amount = fake_paypal.orders.create_payload["body"].purchase_units[0].amount.value
        assert amount == "14.00"

        stored = order_repo.get_model(order_id)
        assert stored is not None
        assert stored.total == 14.0
        assert stored.event_price == 25.0
        assert stored.event_fee == 1.5
        assert stored.discount_code_id == discount.id
        assert stored.discount_code == "MCP50"
        assert stored.discount_amount == 12.5
        assert stored.original_price == 25.0

        raw = db.collection("orders").document(order_id).get().to_dict()
        assert raw["discountCodeId"] == discount.id
        assert raw["discountCode"] == "MCP50"
        assert raw["discountAmount"] == 12.5
        assert raw["originalPrice"] == 25.0
    finally:
        _cleanup_event_flow(event_id, order_id=order_id)


@pytest.mark.integration
def test_create_order_event_rejects_discount_that_would_make_negative_price(
    create_event,
    discount_repo,
):
    event_id = create_event(price=8.0, fee=1.0)
    discount = discount_repo.create(
        event_id,
        {
            "code": "TOO-MUCH",
            "discount_type": "FIXED",
            "discount_value": 10,
            "max_uses": 2,
        },
        admin_uid="admin-test",
    )

    try:
        service = EventPaymentService(paypal_client=_FakePayPalClient(f"ORDER-NEG-{uuid4().hex[:8]}"))
        with pytest.raises(ValidationError, match="Codice sconto non valido per questo importo"):
            service.create_order_event(
                _preorder(event_id, [_participant("buyer-negative@example.com")], discount_code=discount.code)
            )
    finally:
        db.collection("discount_codes").document(discount.id).delete()
        _cleanup_event_flow(event_id)


@pytest.mark.integration
def test_capture_order_event_persists_discount_fields_on_purchase_and_participant(
    create_event,
    discount_admin_service,
    order_repo,
    purchase_repo,
    participant_repo,
    discount_repo,
    created_discounts,
):
    event_id = create_event(price=25.0, fee=1.5)
    discount = _create_discount(
        discount_admin_service,
        created_discounts,
        event_id,
        code="final10",
        discount_type="FIXED_PRICE",
        discount_value=10,
        max_uses=2,
    )
    order_id = f"ORDER-CAPTURE-{uuid4().hex[:8]}"
    buyer_email = "buyer-capture@example.com"
    service = EventPaymentService(paypal_client=_FakePayPalClient(order_id))
    purchase_id = None

    try:
        with patch("services.payments.event_payment_service.ApiHelper.json_serialize", side_effect=lambda body: json.dumps(body)):
            service.create_order_event(_preorder(event_id, [_participant(buyer_email)], discount_code="final10"))

        stored = order_repo.get_model(order_id)
        assert stored is not None
        assert stored.total == 11.5
        assert stored.discount_amount == 15.0
        assert stored.original_price == 25.0

        capture_data = _capture_payload(order_id, event_id, amount=11.5, payer_email=buyer_email)
        with patch.object(service, "capture_paypal_order", return_value=capture_data):
            result = service.capture_order_event(OrderCaptureDTO(orderId=order_id))

        purchase_id = result.purchase_id
        assert purchase_id
        assert order_repo.get_model(order_id) is None

        discount_after = discount_repo.get_by_id(discount.id)
        assert discount_after is not None
        assert discount_after.used_count == 1

        purchase = purchase_repo.get_model(purchase_id)
        assert purchase is not None
        assert purchase.event_id == event_id
        assert purchase.amount_total == "11.50"
        assert purchase.event_purchase_type == EventPurchaseAccessType.PUBLIC
        assert purchase.discount_code_id == discount.id
        assert purchase.discount_code == "FINAL10"
        assert purchase.discount_amount == 15.0
        assert purchase.participants_count == 1

        purchase_raw = db.collection("purchases").document(purchase_id).get().to_dict()
        assert purchase_raw["discountCodeId"] == discount.id
        assert purchase_raw["discountCode"] == "FINAL10"
        assert purchase_raw["discountAmount"] == 15.0
        assert purchase_raw["amount_total"] == "11.50"
        assert purchase_raw["eventPurchaseType"] == EventPurchaseAccessType.PUBLIC.value

        participants = participant_repo.list(event_id)
        assert len(participants) == 1
        participant = participants[0]
        assert participant.purchase_id == purchase_id
        assert participant.email == buyer_email
        assert participant.price == 10.0
        assert participant.price_original == 25.0
        assert participant.discount_code_id == discount.id
        assert participant.discount_code == "FINAL10"

        participant_raw = _event_participants_collection(event_id).document(participant.id).get().to_dict()
        assert participant_raw["purchase_id"] == purchase_id
        assert participant_raw["price"] == 10.0
        assert participant_raw["priceOriginal"] == 25.0
        assert participant_raw["discountCodeId"] == discount.id
        assert participant_raw["discountCode"] == "FINAL10"
        assert "discountAmount" not in participant_raw
    finally:
        _cleanup_event_flow(event_id, order_id=order_id, purchase_id=purchase_id)


@pytest.mark.integration
def test_capture_order_event_rejects_exhausted_discount_race_without_purchase_or_participant(
    create_event,
    discount_admin_service,
    order_repo,
    purchase_repo,
    participant_repo,
    discount_repo,
    created_discounts,
):
    event_id = create_event(price=20.0, fee=1.0)
    discount = _create_discount(
        discount_admin_service,
        created_discounts,
        event_id,
        code="race",
        discount_type="PERCENTAGE",
        discount_value=50,
        max_uses=1,
    )
    order_id = f"ORDER-RACE-{uuid4().hex[:8]}"
    buyer_email = "buyer-race@example.com"
    service = EventPaymentService(paypal_client=_FakePayPalClient(order_id))

    try:
        with patch("services.payments.event_payment_service.ApiHelper.json_serialize", side_effect=lambda body: json.dumps(body)):
            service.create_order_event(_preorder(event_id, [_participant(buyer_email)], discount_code="race"))

        db.collection("discount_codes").document(discount.id).update({"usedCount": 1})
        capture_data = _capture_payload(order_id, event_id, amount=11.0, payer_email=buyer_email)
        with patch.object(service, "capture_paypal_order", return_value=capture_data):
            with pytest.raises(ConflictError, match="Codice sconto esaurito"):
                service.capture_order_event(OrderCaptureDTO(orderId=order_id))

        assert discount_repo.get_by_id(discount.id).used_count == 1
        assert list(purchase_repo.list_models_by_ref_id(event_id)) == []
        assert participant_repo.list(event_id) == []
        assert order_repo.get_model(order_id) is not None
    finally:
        _cleanup_event_flow(event_id, order_id=order_id)
