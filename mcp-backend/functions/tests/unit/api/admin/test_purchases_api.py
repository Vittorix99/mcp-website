import types

from dto.purchase import PurchaseActionResponseDTO, PurchaseDTO
from api.admin import purchases_api
from errors.service_errors import NotFoundError, ValidationError
from models import PurchaseTypes
from tests.utils import DummyRequest, unwrap_response


def _create_body(**overrides):
    body = {
        "payer_name": "Mario",
        "payer_surname": "Rossi",
        "payer_email": "mario@example.com",
        "amount_total": "10.00",
        "currency": "EUR",
        "transaction_id": "tx-1",
        "order_id": "order-1",
        "timestamp": "2026-02-13T10:00:00Z",
    }
    body.update(overrides)
    return body


def test_get_all_purchases_invalid_method():
    resp, status = unwrap_response(purchases_api.get_all_purchases(DummyRequest(method="POST")))
    assert status == 405


def test_get_all_purchases_happy_path(monkeypatch):
    purchase = PurchaseDTO(
        id="pur-1", payer_name="Mario", payer_surname="Rossi", payer_email="mario@example.com",
        amount_total="10.00", currency="EUR", transaction_id="tx-1", order_id="order-1",
        status="COMPLETED", purchase_type=PurchaseTypes.EVENT,
    )
    monkeypatch.setattr(purchases_api, "purchases_service", types.SimpleNamespace(get_all=lambda: [purchase]))
    resp, status = unwrap_response(purchases_api.get_all_purchases(DummyRequest(method="GET")))
    assert status == 200
    assert resp[0]["id"] == "pur-1"


def test_get_purchase_missing_params():
    resp, status = unwrap_response(purchases_api.get_purchase(DummyRequest(method="GET", args={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_get_purchase_invalid_method():
    resp, status = unwrap_response(purchases_api.get_purchase(DummyRequest(method="POST", args={"id": "pur-1"})))
    assert status == 405


def test_get_purchase_happy_path(monkeypatch):
    purchase = PurchaseDTO(
        id="pur-1", payer_name="Mario", payer_surname="Rossi", payer_email="mario@example.com",
        amount_total="10.00", currency="EUR", transaction_id="tx-1", order_id="order-1",
        status="COMPLETED", purchase_type=PurchaseTypes.EVENT,
    )
    monkeypatch.setattr(
        purchases_api, "purchases_service",
        types.SimpleNamespace(get_by_id=lambda purchase_id, slug=None: purchase),
    )
    resp, status = unwrap_response(purchases_api.get_purchase(DummyRequest(method="GET", args={"id": "pur-1"})))
    assert status == 200
    assert resp["id"] == "pur-1"


def test_create_purchase_missing_body():
    resp, status = unwrap_response(purchases_api.create_purchase(DummyRequest(method="POST")))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_create_purchase_validation_error(monkeypatch):
    monkeypatch.setattr(
        purchases_api, "purchases_service",
        types.SimpleNamespace(create=lambda dto: (_ for _ in ()).throw(ValidationError("bad"))),
    )
    resp, status = unwrap_response(
        purchases_api.create_purchase(DummyRequest(method="POST", json=_create_body()))
    )
    assert status == 400
    assert resp["error"] == "bad"


def test_create_purchase_happy_path(monkeypatch):
    captured = {}

    def create(dto):
        captured["dto"] = dto
        return PurchaseActionResponseDTO(message="Purchase created", id="pur-1")

    monkeypatch.setattr(purchases_api, "purchases_service", types.SimpleNamespace(create=create))
    resp, status = unwrap_response(
        purchases_api.create_purchase(DummyRequest(method="POST", json=_create_body()))
    )
    assert status == 201
    assert resp == {"message": "Purchase created", "id": "pur-1"}
    assert captured["dto"].purchase_type == "event"


def test_create_purchase_rejects_invalid_type():
    resp, status = unwrap_response(
        purchases_api.create_purchase(
            DummyRequest(method="POST", json=_create_body(purchase_type="invalid-type"))
        )
    )
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_delete_purchase_missing_id():
    resp, status = unwrap_response(purchases_api.delete_purchase(DummyRequest(method="DELETE", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_delete_purchase_not_found(monkeypatch):
    monkeypatch.setattr(
        purchases_api, "purchases_service",
        types.SimpleNamespace(delete=lambda pid: (_ for _ in ()).throw(NotFoundError("missing"))),
    )
    resp, status = unwrap_response(
        purchases_api.delete_purchase(DummyRequest(method="DELETE", json={"purchase_id": "pur-1"}))
    )
    assert status == 404
    assert resp["error"] == "missing"


def test_delete_purchase_happy_path(monkeypatch):
    monkeypatch.setattr(
        purchases_api, "purchases_service",
        types.SimpleNamespace(delete=lambda pid: PurchaseActionResponseDTO(message="Purchase deleted", id=pid)),
    )
    resp, status = unwrap_response(
        purchases_api.delete_purchase(DummyRequest(method="DELETE", json={"purchase_id": "pur-1"}))
    )
    assert status == 200
    assert resp == {"message": "Purchase deleted", "id": "pur-1"}
