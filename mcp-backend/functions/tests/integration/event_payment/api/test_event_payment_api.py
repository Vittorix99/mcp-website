import pytest

from api.public import event_payment_api
from dto import PreOrderCartItemDTO, PreOrderDTO
from models import EventPurchaseAccessType
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_event_payment_api_create_order_public(
    paypal_env,
    create_event,
    participant,
    order_repository,
):
    """Creates a PayPal order via the public API and stores staging data."""
    event_id = create_event()
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId=event_id, participants=[participant])]).to_payload()
    req = DummyRequest(method="POST", json=payload)

    resp, status = unwrap_response(event_payment_api.create_order_event(req))
    assert status == 201
    order_id = resp.get("id")
    assert order_id

    stored = order_repository.get(order_id)
    assert stored is not None
    assert stored.get("eventId") == event_id

    order_repository.delete(order_id)


@pytest.mark.integration
def test_event_payment_api_rejects_underage_participants(
    create_event,
    underage_participant,
):
    """Rejects under-21 participants when event requires 21+."""
    event_id = create_event(over21Only=True)
    payload = PreOrderDTO(
        cart=[PreOrderCartItemDTO(eventId=event_id, participants=[underage_participant])]
    ).to_payload()
    req = DummyRequest(method="POST", json=payload)

    resp, status = unwrap_response(event_payment_api.create_order_event(req))
    assert status == 400
    assert resp.get("error") == "validation_error"
    messages = resp.get("messages") or []
    assert any("maggiori di 21 anni" in msg for msg in messages)


@pytest.mark.integration
def test_event_payment_api_capture_unapproved_order(
    paypal_env,
    create_event,
    participant,
    order_repository,
):
    """Capturing a non-approved PayPal order returns an upstream error."""
    event_id = create_event(purchaseMode=EventPurchaseAccessType.PUBLIC.value)
    payload = PreOrderDTO(cart=[PreOrderCartItemDTO(eventId=event_id, participants=[participant])]).to_payload()
    create_req = DummyRequest(method="POST", json=payload)
    resp, status = unwrap_response(event_payment_api.create_order_event(create_req))
    assert status == 201
    order_id = resp.get("id")
    assert order_id

    capture_req = DummyRequest(method="POST", json={"order_id": order_id})
    resp, status = unwrap_response(event_payment_api.capture_order_event(capture_req))
    assert status == 502
    assert "Failed to capture order" in resp.get("error", "")

    order_repository.delete(order_id)
