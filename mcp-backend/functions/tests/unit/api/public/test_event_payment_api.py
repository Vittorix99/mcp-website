from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from api.public import event_payment_api
from dto.preorder import EventOrderCreateResponseDTO, OrderCaptureResponseDTO
from errors.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def _create_logic():
    # Isolate DTO/service mapping; method guards use the exported endpoint.
    handler = event_payment_api.create_order_event
    while hasattr(handler, "__wrapped__"):
        handler = handler.__wrapped__
    return handler


def _order_request():
    req = DummyRequest(method="POST", json={"cart": [{
        "eventId": "evt-1", "participants": [{
            "name": "Mario", "surname": "Rossi", "email": "mario@example.com",
            "phone": "+393331234567", "birthdate": "01-01-1990",
        }],
    }]})
    req.event_data = {"title": "Test"}
    req.event_id = "evt-1"
    return req


@pytest.mark.parametrize("endpoint", ["create_order_event", "capture_order_event"])
def test_payment_endpoint_rejects_invalid_method(endpoint):
    _, status = unwrap_response(getattr(event_payment_api, endpoint)(DummyRequest(method="GET")))
    assert status == 405


@pytest.mark.parametrize("payload", [None, {}, {"cart": []}])
def test_create_order_rejects_invalid_body_before_service(monkeypatch, payload):
    create = Mock()
    monkeypatch.setattr(event_payment_api, "event_payment_service", SimpleNamespace(create_order_event=create))
    response, status = unwrap_response(_create_logic()(DummyRequest(method="POST", json=payload)))
    assert status == 400
    assert response["error"] == "Invalid request data"
    assert response["details"]
    create.assert_not_called()


def test_create_order_event_happy_path(monkeypatch):
    create = Mock(return_value=EventOrderCreateResponseDTO(id="order-1", status="CREATED"))
    monkeypatch.setattr(event_payment_api, "event_payment_service", SimpleNamespace(create_order_event=create))
    response, status = unwrap_response(_create_logic()(_order_request()))
    assert status == 201
    assert response == {"id": "order-1", "status": "CREATED", "links": []}
    create.assert_called_once()
    order, event = create.call_args.args
    assert order.cart[0].event_id == "evt-1"
    assert order.cart[0].participants[0].email == "mario@example.com"
    assert event.id == "evt-1"
    assert event.title == "Test"


@pytest.mark.parametrize("error, expected_status", [
    (ValidationError("validation_error"), 400),
    (NotFoundError("missing"), 404),
    (ExternalServiceError("upstream failed"), 502),
    (ServiceError("service failed"), 500),
])
def test_create_order_maps_service_errors(monkeypatch, error, expected_status):
    if isinstance(error, ValidationError):
        error.details = ["bad"]
    create = Mock(side_effect=error)
    monkeypatch.setattr(event_payment_api, "event_payment_service", SimpleNamespace(create_order_event=create))
    response, status = unwrap_response(_create_logic()(_order_request()))
    assert status == expected_status
    assert response["error"] == str(error)
    if isinstance(error, ValidationError):
        assert response["messages"] == ["bad"]
    create.assert_called_once()


def test_capture_order_event_missing_body(monkeypatch):
    capture = Mock()
    monkeypatch.setattr(event_payment_api, "event_payment_service", SimpleNamespace(capture_order_event=capture))
    response, status = unwrap_response(event_payment_api.capture_order_event(DummyRequest(method="POST", json=None)))
    assert status == 400
    assert response["error"] == "Invalid request data"
    capture.assert_not_called()


def test_capture_order_event_happy_path(monkeypatch):
    capture = Mock(return_value=OrderCaptureResponseDTO(message="captured", purchase_id="purchase-1"))
    monkeypatch.setattr(event_payment_api, "event_payment_service", SimpleNamespace(capture_order_event=capture))
    response, status = unwrap_response(event_payment_api.capture_order_event(
        DummyRequest(method="POST", json={"order_id": "order-1"})))
    assert status == 200
    assert response == {"message": "captured", "purchase_id": "purchase-1"}
    capture.assert_called_once()
    assert capture.call_args.args[0].order_id == "order-1"


def test_capture_order_event_validation_error(monkeypatch):
    capture = Mock(side_effect=ValidationError("bad"))
    monkeypatch.setattr(event_payment_api, "event_payment_service", SimpleNamespace(capture_order_event=capture))
    response, status = unwrap_response(event_payment_api.capture_order_event(
        DummyRequest(method="POST", json={"order_id": "order-1"})))
    assert status == 400
    assert response["error"] == "bad"
    capture.assert_called_once()
