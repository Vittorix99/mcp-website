import types

from api.admin import purchases_api
from services.service_errors import NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_all_purchases_invalid_method():
    """Rejects invalid method for listing purchases."""
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(purchases_api.get_all_purchases(req))
    assert status == 405


def test_get_all_purchases_happy_path(monkeypatch):
    """Returns all purchases."""
    monkeypatch.setattr(
        purchases_api,
        "purchases_service",
        types.SimpleNamespace(get_all=lambda: [{"id": "pur-1"}]),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(purchases_api.get_all_purchases(req))
    assert status == 200
    assert resp == [{"id": "pur-1"}]


def test_get_purchase_missing_params():
    """Returns 400 when id/slug are missing."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(purchases_api.get_purchase(req))
    assert status == 400
    assert resp["error"] == "Missing purchase_id or slug"


def test_create_purchase_missing_body(monkeypatch):
    """Returns 400 when body is missing."""
    monkeypatch.setattr(purchases_api.request, "get_json", lambda: None)
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(purchases_api.create_purchase(req))
    assert status == 400
    assert resp["error"] == "Missing JSON body"


def test_create_purchase_validation_error(monkeypatch):
    """Maps validation errors to 400."""
    monkeypatch.setattr(
        purchases_api,
        "purchases_service",
        types.SimpleNamespace(create=lambda dto: (_ for _ in ()).throw(ValidationError("bad"))),
    )
    monkeypatch.setattr(purchases_api.request, "get_json", lambda: {"payer_name": "Mario"})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(purchases_api.create_purchase(req))
    assert status == 400
    assert resp["error"] == "bad"


def test_delete_purchase_missing_id(monkeypatch):
    """Returns 400 when purchase_id is missing."""
    monkeypatch.setattr(purchases_api.request, "get_json", lambda: {})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(purchases_api.delete_purchase(req))
    assert status == 400
    assert resp["error"] == "Missing purchase_id"


def test_delete_purchase_not_found(monkeypatch):
    """Maps not found errors to 404."""
    monkeypatch.setattr(
        purchases_api,
        "purchases_service",
        types.SimpleNamespace(delete=lambda pid: (_ for _ in ()).throw(NotFoundError("missing"))),
    )
    monkeypatch.setattr(purchases_api.request, "get_json", lambda: {"purchase_id": "pur-1"})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(purchases_api.delete_purchase(req))
    assert status == 404
    assert resp["error"] == "missing"
