import pytest

from api.admin import purchases_api
from models import PurchaseStatus
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_purchases_api_crud(purchase_payload):
    """Creates, fetches, lists, and deletes purchases via admin API."""
    purchase_id = None
    try:
        create_req = DummyRequest(method="POST", json=purchase_payload)
        resp, status = unwrap_response(purchases_api.create_purchase(create_req))
        assert status == 201
        purchase_id = resp.get("id")
        assert purchase_id

        get_req = DummyRequest(method="GET", args={"id": purchase_id})
        resp, status = unwrap_response(purchases_api.get_purchase(get_req))
        assert status == 200
        assert resp.get("id") == purchase_id

        list_req = DummyRequest(method="GET")
        resp, status = unwrap_response(purchases_api.get_all_purchases(list_req))
        assert status == 200
        assert any(item.get("id") == purchase_id for item in resp)
    finally:
        if purchase_id:
            delete_req = DummyRequest(method="DELETE", json={"purchase_id": purchase_id})
            unwrap_response(purchases_api.delete_purchase(delete_req))


@pytest.mark.integration
def test_purchases_api_missing_id():
    """Returns 400 when id/slug is missing."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(purchases_api.get_purchase(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_purchases_api_update_status(purchase_payload, purchase_repository):
    """Updates a purchase status through the admin API."""
    purchase_id = None
    try:
        create_req = DummyRequest(method="POST", json=purchase_payload)
        resp, status = unwrap_response(purchases_api.create_purchase(create_req))
        assert status == 201
        purchase_id = resp.get("id")
        assert purchase_id

        update_req = DummyRequest(
            method="POST",
            json={"purchase_id": purchase_id, "status": PurchaseStatus.REFUNDED.value},
        )
        resp, status = unwrap_response(purchases_api.update_purchase_status(update_req))
        assert status == 200
        assert resp.get("id") == purchase_id
        assert resp.get("message") == "Status updated"

        updated = purchase_repository.get_model(purchase_id)
        assert updated is not None
        assert updated.status == PurchaseStatus.REFUNDED.value
    finally:
        if purchase_id:
            delete_req = DummyRequest(method="DELETE", json={"purchase_id": purchase_id})
            unwrap_response(purchases_api.delete_purchase(delete_req))


@pytest.mark.integration
def test_purchases_api_update_status_rejects_invalid_status(purchase_payload):
    """Returns 400 when updating a purchase to an unsupported status."""
    create_req = DummyRequest(method="POST", json=purchase_payload)
    resp, status = unwrap_response(purchases_api.create_purchase(create_req))
    assert status == 201
    purchase_id = resp.get("id")

    try:
        update_req = DummyRequest(
            method="POST",
            json={"purchase_id": purchase_id, "status": "NOT_A_REAL_STATUS"},
        )
        resp, status = unwrap_response(purchases_api.update_purchase_status(update_req))
        assert status == 400
        assert resp.get("error")
    finally:
        if purchase_id:
            delete_req = DummyRequest(method="DELETE", json={"purchase_id": purchase_id})
            unwrap_response(purchases_api.delete_purchase(delete_req))
