import pytest

from api.admin import members_api
from dto import MembershipDTO
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_memberships_api_crud(membership_payload, monkeypatch):
    """Creates, fetches, updates, lists, and deletes a membership via admin API."""
    membership_id = None
    try:
        monkeypatch.setattr(members_api.request, "get_json", lambda: membership_payload)
        create_req = DummyRequest(method="POST")
        resp, status = unwrap_response(members_api.create_membership(create_req))
        assert status == 201
        membership_id = resp.get("id")
        assert membership_id

        get_req = DummyRequest(method="GET", args={"id": membership_id})
        resp, status = unwrap_response(members_api.get_membership(get_req))
        assert status == 200
        assert resp.get("id") == membership_id

        monkeypatch.setattr(
            members_api.request,
            "get_json",
            lambda: {"membership_id": membership_id, "phone": "+390000000222"},
        )
        update_req = DummyRequest(method="PUT")
        resp, status = unwrap_response(members_api.update_membership(update_req))
        assert status == 200

        list_req = DummyRequest(method="GET")
        resp, status = unwrap_response(members_api.get_memberships(list_req))
        assert status == 200
        assert any(item.get("id") == membership_id for item in resp)
    finally:
        if membership_id:
            monkeypatch.setattr(
                members_api.request,
                "get_json",
                lambda: {"membership_id": membership_id},
            )
            delete_req = DummyRequest(method="DELETE")
            unwrap_response(members_api.delete_membership(delete_req))


@pytest.mark.integration
def test_memberships_api_missing_id():
    """Returns 400 when id/slug is missing."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(members_api.get_membership(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_memberships_api_set_get_price(monkeypatch):
    """Sets and retrieves the membership price via admin API."""
    monkeypatch.setattr(
        members_api.request,
        "get_json",
        lambda: {"membership_fee": 30.0, "year": "2026"},
    )
    set_req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_membership_price(set_req))
    assert status == 200

    get_req = DummyRequest(method="GET", args={"year": "2026"})
    resp, status = unwrap_response(members_api.get_membership_price(get_req))
    assert status == 200
    assert resp.get("price") == 30.0


@pytest.mark.integration
def test_memberships_api_get_purchases_and_events(
    memberships_service,
    membership_repository,
    membership_payload,
    create_membership,
    create_purchase,
    create_event,
):
    """Returns purchases and events linked to a membership via admin API."""
    membership_id = create_membership(membership_payload)
    purchase_id = create_purchase()
    event_id = create_event()

    membership_repository.update_from_model(
        membership_id,
        MembershipDTO(purchases=[purchase_id], attended_events=[event_id]),
    )

    purchases_req = DummyRequest(method="GET", args={"id": membership_id})
    resp, status = unwrap_response(members_api.get_membership_purchases(purchases_req))
    assert status == 200
    assert any(item.get("id") == purchase_id for item in resp)

    events_req = DummyRequest(method="GET", args={"id": membership_id})
    resp, status = unwrap_response(members_api.get_membership_events(events_req))
    assert status == 200
    assert any(item.get("id") == event_id for item in resp)
