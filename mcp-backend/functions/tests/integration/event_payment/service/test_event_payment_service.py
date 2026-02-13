import pytest

from dto import PreOrderCartItemDTO, PreOrderDTO
from models import EventPurchaseAccessType
from services.event_payment_service import EventPaymentService
from services.service_errors import ValidationError


@pytest.mark.integration
def test_event_payment_service_create_order_public(paypal_env, create_event, participant, order_repository):
    """Creates a PayPal order for a public event and stores a staging order."""
    event_id = create_event()
    service = EventPaymentService()

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId=event_id, participants=[participant])])
    result = service.create_order_event(payload)
    order_id = result.get("id")
    assert order_id

    stored = order_repository.get(order_id)
    assert stored is not None
    assert stored.get("eventId") == event_id

    order_repository.delete(order_id)


@pytest.mark.integration
def test_event_payment_service_only_members_creates_targets(
    paypal_env,
    create_event,
    participant,
    order_repository,
    ensure_membership_fee,
):
    """Adds membership targets and fee for ONLY_MEMBERS events."""
    event_id = create_event(purchaseMode=EventPurchaseAccessType.ONLY_MEMBERS.value)
    service = EventPaymentService()

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId=event_id, participants=[participant])])
    result = service.create_order_event(payload)
    order_id = result.get("id")
    assert order_id

    stored = order_repository.get(order_id)
    assert stored is not None
    assert stored.get("membershipFee") == ensure_membership_fee
    targets = stored.get("membershipTargets") or []
    assert len(targets) == 1

    order_repository.delete(order_id)


@pytest.mark.integration
def test_event_payment_service_only_registered_members_rejected(create_event, participant):
    """Rejects non-members for ONLY_ALREADY_REGISTERED_MEMBERS events."""
    event_id = create_event(purchaseMode=EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS.value)
    service = EventPaymentService()

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId=event_id, participants=[participant])])
    with pytest.raises(ValidationError):
        service.create_order_event(payload)


@pytest.mark.integration
def test_event_payment_service_only_registered_members_accepts_member(
    paypal_env,
    create_event,
    participant,
    member_record,
    order_repository,
):
    """Accepts existing members for ONLY_ALREADY_REGISTERED_MEMBERS events."""
    event_id = create_event(purchaseMode=EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS.value)
    service = EventPaymentService()

    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId=event_id, participants=[participant])])
    result = service.create_order_event(payload)
    order_id = result.get("id")
    assert order_id

    stored = order_repository.get(order_id)
    assert stored is not None
    lookup = stored.get("membershipLookup") or {}
    assert participant.email in lookup

    order_repository.delete(order_id)
