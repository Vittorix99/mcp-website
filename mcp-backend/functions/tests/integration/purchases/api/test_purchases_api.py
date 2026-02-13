import pytest

from api.admin import purchases_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_purchases_api_crud(purchase_dto, monkeypatch):
    """Creates, fetches, lists, and deletes purchases via admin API."""
    purchase_id = None
    try:
        monkeypatch.setattr(purchases_api.request, "get_json", lambda: purchase_dto.to_payload())
        create_req = DummyRequest(method="POST")
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
            monkeypatch.setattr(purchases_api.request, "get_json", lambda: {"purchase_id": purchase_id})
            delete_req = DummyRequest(method="DELETE")
            unwrap_response(purchases_api.delete_purchase(delete_req))


@pytest.mark.integration
def test_purchases_api_missing_id():
    """Returns 400 when id/slug is missing."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(purchases_api.get_purchase(req))
    assert status == 400
    assert resp.get("error")
