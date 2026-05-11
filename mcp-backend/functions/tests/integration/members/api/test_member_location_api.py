import pytest

from api.member import location_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_get_location_returns_published_location(create_event, seed_location):
    """Returns location fields when location is published."""
    event_id = create_event()
    seed_location(event_id, published=True)

    req = DummyRequest(method="GET", args={"event_id": event_id})
    resp, status = unwrap_response(location_api.member_get_event_location(req))

    assert status == 200
    assert resp.get("label") == "Warehouse 23"
    assert resp.get("address") == "Via Test 1, Milano"
    assert resp.get("maps_url") == "https://maps.google.com/?q=test"
    assert resp.get("hint") == "Ingresso principale"


@pytest.mark.integration
def test_get_location_returns_404_when_not_published(create_event, seed_location):
    """Returns 404 when location exists but is not published."""
    event_id = create_event()
    seed_location(event_id, published=False)

    req = DummyRequest(method="GET", args={"event_id": event_id})
    resp, status = unwrap_response(location_api.member_get_event_location(req))

    assert status == 404


@pytest.mark.integration
def test_get_location_returns_404_when_no_location_doc(create_event):
    """Returns 404 when no location document exists for the event."""
    event_id = create_event()

    req = DummyRequest(method="GET", args={"event_id": event_id})
    resp, status = unwrap_response(location_api.member_get_event_location(req))

    assert status == 404


@pytest.mark.integration
def test_get_location_missing_event_id_returns_400():
    """Missing event_id query param returns 400."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(location_api.member_get_event_location(req))
    assert status == 400


@pytest.mark.integration
def test_get_location_wrong_method_returns_405():
    """Non-GET requests return 405."""
    req = DummyRequest(method="POST", args={"event_id": "any"})
    resp, status = unwrap_response(location_api.member_get_event_location(req))
    assert status == 405


@pytest.mark.integration
def test_get_location_no_auth_returns_401():
    """Missing Authorization header returns 401."""
    req = DummyRequest(method="GET", args={"event_id": "any"}, headers={"Authorization": "no-token"})
    resp, status = unwrap_response(location_api.member_get_event_location(req))
    assert status == 401
