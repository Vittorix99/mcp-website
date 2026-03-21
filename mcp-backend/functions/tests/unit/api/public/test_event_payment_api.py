from api.public import event_payment_api
from errors.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def _unwrap(func):
    handler = func
    while hasattr(handler, "__wrapped__"):
        handler = handler.__wrapped__
    return handler


def test_create_order_event_invalid_method():
    """Rejects non-POST methods for create order."""
    handler = _unwrap(event_payment_api.create_order_event)
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(handler(req))
    assert status == 405


def test_create_order_event_missing_body():
    """Returns 400 when request body is missing."""
    handler = _unwrap(event_payment_api.create_order_event)
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(handler(req))
    assert status == 400
    assert resp["error"] == "Missing request body"


def test_create_order_event_happy_path(monkeypatch):
    """Creates a PayPal order when payload is valid."""
    handler = _unwrap(event_payment_api.create_order_event)
    monkeypatch.setattr(
        event_payment_api,
        "create_order_event_service",
        lambda order_dto, event_dto: {"id": "order-1"},
    )
    req = DummyRequest(
        method="POST",
        json={
            "cart": [
                {
                    "eventId": "evt-1",
                    "participants": [
                        {
                            "name": "Mario",
                            "surname": "Rossi",
                            "email": "mario@example.com",
                            "phone": "+390000000000",
                            "birthdate": "01-01-1990",
                        }
                    ],
                }
            ]
        },
    )
    req.event_payload = {
        "cart": [
            {
                "eventId": "evt-1",
                "participants": [
                    {
                        "name": "Mario",
                        "surname": "Rossi",
                        "email": "mario@example.com",
                        "phone": "+390000000000",
                        "birthdate": "01-01-1990",
                    }
                ],
            }
        ]
    }
    req.event_data = {"title": "Test"}
    req.event_id = "evt-1"
    resp, status = unwrap_response(handler(req))
    assert status == 201
    assert resp["id"] == "order-1"


def test_create_order_event_validation_error(monkeypatch):
    """Maps validation errors with details to 400 response."""
    handler = _unwrap(event_payment_api.create_order_event)
    err = ValidationError("validation_error")
    err.details = ["bad"]
    monkeypatch.setattr(
        event_payment_api,
        "create_order_event_service",
        lambda order_dto, event_dto: (_ for _ in ()).throw(err),
    )
    req = DummyRequest(method="POST", json={"cart": []})
    req.event_payload = {"cart": []}
    resp, status = unwrap_response(handler(req))
    assert status == 400
    assert resp["error"] == "validation_error"
    assert resp["messages"] == ["bad"]


def test_create_order_event_not_found(monkeypatch):
    """Maps not found errors to 404 response."""
    handler = _unwrap(event_payment_api.create_order_event)
    monkeypatch.setattr(
        event_payment_api,
        "create_order_event_service",
        lambda order_dto, event_dto: (_ for _ in ()).throw(NotFoundError("missing")),
    )
    req = DummyRequest(method="POST", json={"cart": []})
    req.event_payload = {"cart": []}
    resp, status = unwrap_response(handler(req))
    assert status == 404
    assert resp["error"] == "missing"


def test_create_order_event_external_error(monkeypatch):
    """Maps upstream errors to 502 response."""
    handler = _unwrap(event_payment_api.create_order_event)
    monkeypatch.setattr(
        event_payment_api,
        "create_order_event_service",
        lambda order_dto, event_dto: (_ for _ in ()).throw(ExternalServiceError("boom")),
    )
    req = DummyRequest(method="POST", json={"cart": []})
    req.event_payload = {"cart": []}
    resp, status = unwrap_response(handler(req))
    assert status == 502
    assert resp["error"] == "boom"


def test_create_order_event_service_error(monkeypatch):
    """Maps generic service errors to 500 response."""
    handler = _unwrap(event_payment_api.create_order_event)
    monkeypatch.setattr(
        event_payment_api,
        "create_order_event_service",
        lambda order_dto, event_dto: (_ for _ in ()).throw(ServiceError("boom")),
    )
    req = DummyRequest(method="POST", json={"cart": []})
    req.event_payload = {"cart": []}
    resp, status = unwrap_response(handler(req))
    assert status == 500
    assert resp["error"] == "boom"


def test_capture_order_event_missing_body():
    """Returns 400 when capture body is missing."""
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(event_payment_api.capture_order_event(req))
    assert status == 400
    assert resp["error"] == "Missing request body"


def test_capture_order_event_invalid_method():
    """Rejects non-POST methods for capture."""
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(event_payment_api.capture_order_event(req))
    assert status == 405


def test_capture_order_event_happy_path(monkeypatch):
    """Returns 200 when capture succeeds."""
    monkeypatch.setattr(
        event_payment_api,
        "capture_order_event_service",
        lambda capture_dto: {"ok": True},
    )
    req = DummyRequest(method="POST", json={"order_id": "order-1"})
    resp, status = unwrap_response(event_payment_api.capture_order_event(req))
    assert status == 200
    assert resp["ok"] is True


def test_capture_order_event_validation_error(monkeypatch):
    """Maps validation errors on capture to 400 response."""
    monkeypatch.setattr(
        event_payment_api,
        "capture_order_event_service",
        lambda capture_dto: (_ for _ in ()).throw(ValidationError("bad")),
    )
    req = DummyRequest(method="POST", json={"order_id": "order-1"})
    resp, status = unwrap_response(event_payment_api.capture_order_event(req))
    assert status == 400
    assert resp["error"] == "bad"
