import pytest

from api.member import member_api
from tests.utils import DummyRequest, unwrap_response


# ---------------------------------------------------------------------------
# member_get_me
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_me_returns_correct_data(create_membership):
    """GET /member/me returns membership fields for the authenticated email."""
    create_membership(name="Luigi", surname="Verdi")
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(member_api.member_get_me(req))

    assert status == 200
    assert resp.get("name") == "Luigi"
    assert resp.get("surname") == "Verdi"
    assert resp.get("subscription_valid") is True
    assert "email" in resp
    assert "id" in resp


@pytest.mark.integration
def test_get_me_no_membership_returns_404(monkeypatch, member_email):
    """Auth with an email that has no membership returns 404."""
    # Override token to return an email with no membership in Firestore
    import api.decorators as _dec
    monkeypatch.setattr(
        _dec.fb_auth,
        "verify_id_token",
        lambda _token: {"uid": "ghost-uid", "email": f"ghost_{member_email}"},
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(member_api.member_get_me(req))
    assert status == 404


@pytest.mark.integration
def test_get_me_no_auth_returns_401():
    """Missing Authorization header returns 401."""
    req = DummyRequest(method="GET", headers={"Authorization": "no-token"})
    resp, status = unwrap_response(member_api.member_get_me(req))
    assert status == 401


@pytest.mark.integration
def test_get_me_wrong_method_returns_405():
    """Non-GET requests return 405."""
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(member_api.member_get_me(req))
    assert status == 405


# ---------------------------------------------------------------------------
# member_get_events
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_events_returns_attended_events(
    create_membership, membership_repository, create_event
):
    """Returns attended events list after linking event to membership."""
    membership_id = create_membership()
    event_id = create_event()
    membership_repository.add_attended_event(membership_id, event_id)

    req = DummyRequest(method="GET")
    resp, status = unwrap_response(member_api.member_get_events(req))

    assert status == 200
    assert isinstance(resp, list)
    ids = [item.get("id") for item in resp]
    assert event_id in ids


@pytest.mark.integration
def test_get_events_empty_when_no_attended(create_membership):
    """Fresh membership with no attended events returns empty list."""
    create_membership(attended_events=[])
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(member_api.member_get_events(req))

    assert status == 200
    assert resp == []


@pytest.mark.integration
def test_get_events_wrong_method_returns_405():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(member_api.member_get_events(req))
    assert status == 405


# ---------------------------------------------------------------------------
# member_get_purchases
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_purchases_returns_purchases(
    create_membership, membership_repository, purchase_repository
):
    """Returns purchases list after linking purchase to membership."""
    from models import Purchase, PurchaseTypes
    from uuid import uuid4

    membership_id = create_membership()

    suffix = uuid4().hex[:8]
    purchase = Purchase(
        payer_name="Mario",
        payer_surname="Rossi",
        payer_email="test@example.com",
        amount_total="15.00",
        currency="EUR",
        transaction_id=f"txn-{suffix}",
        order_id=f"order-{suffix}",
        status="COMPLETED",
        purchase_type=PurchaseTypes.EVENT,
        ref_id=f"event-{suffix}",
        payment_method="website",
        capture_status="COMPLETED",
    )
    purchase_id = purchase_repository.create_from_model(purchase)

    try:
        membership_repository.add_attended_event_and_purchase(membership_id, f"event-{suffix}", purchase_id)

        req = DummyRequest(method="GET")
        resp, status = unwrap_response(member_api.member_get_purchases(req))

        assert status == 200
        assert isinstance(resp, list)
        ids = [item.get("id") for item in resp]
        assert purchase_id in ids

        entry = next(item for item in resp if item["id"] == purchase_id)
        assert entry.get("amount_total") == "15.00"
        assert entry.get("currency") == "EUR"
    finally:
        purchase_repository.delete(purchase_id)


@pytest.mark.integration
def test_get_purchases_empty_when_none(create_membership):
    """Fresh membership with no purchases returns empty list."""
    create_membership(purchases=[])
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(member_api.member_get_purchases(req))

    assert status == 200
    assert resp == []


@pytest.mark.integration
def test_get_purchases_wrong_method_returns_405():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(member_api.member_get_purchases(req))
    assert status == 405


# ---------------------------------------------------------------------------
# member_get_ticket
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_ticket_is_participant_when_linked(
    create_membership, create_event, create_participant
):
    """Returns is_participant=True when a participant entry exists linked by membership_id."""
    membership_id = create_membership()
    event_id = create_event()
    create_participant(event_id, membership_id)

    req = DummyRequest(method="GET", args={"event_id": event_id})
    resp, status = unwrap_response(member_api.member_get_ticket(req))

    assert status == 200
    assert resp.get("is_participant") is True


@pytest.mark.integration
def test_get_ticket_not_participant_when_no_entry(create_membership, create_event):
    """Returns is_participant=False when no participant entry exists for this membership."""
    create_membership()
    event_id = create_event()

    req = DummyRequest(method="GET", args={"event_id": event_id})
    resp, status = unwrap_response(member_api.member_get_ticket(req))

    assert status == 200
    assert resp.get("is_participant") is False


@pytest.mark.integration
def test_get_ticket_missing_event_id_returns_400(create_membership):
    """Missing event_id query param returns 400."""
    create_membership()
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(member_api.member_get_ticket(req))
    assert status == 400


@pytest.mark.integration
def test_get_ticket_wrong_method_returns_405():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(member_api.member_get_ticket(req))
    assert status == 405


# ---------------------------------------------------------------------------
# member_patch_preferences
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_patch_preferences_updates_newsletter_consent(
    create_membership, membership_repository
):
    """PATCH preferences updates newsletter_consent in Firestore."""
    membership_id = create_membership(newsletter_consent=True)

    req = DummyRequest(method="PATCH", json={"newsletter_consent": False})
    resp, status = unwrap_response(member_api.member_patch_preferences(req))

    assert status == 200
    assert resp.get("success") is True

    updated = membership_repository.get(membership_id)
    assert updated.newsletter_consent is False


@pytest.mark.integration
def test_patch_preferences_wrong_method_returns_405():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(member_api.member_patch_preferences(req))
    assert status == 405


@pytest.mark.integration
def test_patch_preferences_missing_field_returns_400(create_membership):
    """Missing newsletter_consent field returns 400."""
    create_membership()
    req = DummyRequest(method="PATCH", json={})
    resp, status = unwrap_response(member_api.member_patch_preferences(req))
    assert status == 400
