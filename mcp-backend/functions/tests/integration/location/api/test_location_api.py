import pytest

from api.admin import location_api, participants_api
from config.firebase_config import db
from tests.utils import DummyRequest, unwrap_response


# ---------------------------------------------------------------------------
# admin_get_event_location
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_location_no_doc_returns_empty_fields(create_event):
    """Valid event with no location document returns 200 with empty fields."""
    event_id = create_event()

    req = DummyRequest(method="GET", args={"event_id": event_id})
    resp, status = unwrap_response(location_api.admin_get_event_location(req))

    assert status == 200
    assert resp.get("label") == ""
    assert resp.get("maps_url") == ""
    assert resp.get("address") == ""
    assert resp.get("published") is False


@pytest.mark.integration
def test_get_location_nonexistent_event_returns_404():
    """Non-existent event_id returns 404."""
    req = DummyRequest(method="GET", args={"event_id": "ghost-event-id"})
    resp, status = unwrap_response(location_api.admin_get_event_location(req))

    assert status == 404


@pytest.mark.integration
def test_get_location_missing_event_id_returns_400():
    """Missing event_id query param returns 400."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(location_api.admin_get_event_location(req))

    assert status == 400


@pytest.mark.integration
def test_get_location_wrong_method_returns_405():
    """Non-GET request returns 405."""
    req = DummyRequest(method="POST", args={"event_id": "any"})
    resp, status = unwrap_response(location_api.admin_get_event_location(req))

    assert status == 405


# ---------------------------------------------------------------------------
# admin_update_event_location
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_update_location_saves_fields(create_event):
    """PUT update saves fields and returns them in the response."""
    event_id = create_event()
    payload = {
        "event_id": event_id,
        "label": "Warehouse 42",
        "maps_url": "https://maps.google.com/?q=warehouse42",
        "maps_embed_url": "https://maps.google.com/embed?q=warehouse42",
        "address": "Via Roma 1, Milano",
        "message": "Porta il biglietto",
    }

    req = DummyRequest(method="PUT", json=payload)
    resp, status = unwrap_response(location_api.admin_update_event_location(req))

    assert status == 200
    assert resp.get("label") == "Warehouse 42"
    assert resp.get("address") == "Via Roma 1, Milano"
    assert resp.get("maps_url") == "https://maps.google.com/?q=warehouse42"
    assert resp.get("message") == "Porta il biglietto"


@pytest.mark.integration
def test_update_location_nonexistent_event_returns_404():
    """Non-existent event_id returns 404."""
    req = DummyRequest(method="PUT", json={"event_id": "ghost-event-id", "label": "X"})
    resp, status = unwrap_response(location_api.admin_update_event_location(req))

    assert status == 404


@pytest.mark.integration
def test_update_location_missing_event_id_returns_400():
    """Missing event_id returns 400."""
    req = DummyRequest(method="PUT", json={"label": "No event"})
    resp, status = unwrap_response(location_api.admin_update_event_location(req))

    assert status == 400


@pytest.mark.integration
def test_update_location_wrong_method_returns_405():
    """Non-PUT request returns 405."""
    req = DummyRequest(method="GET", json={"event_id": "any"})
    resp, status = unwrap_response(location_api.admin_update_event_location(req))

    assert status == 405


# ---------------------------------------------------------------------------
# admin_toggle_location_published
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_toggle_location_publish_sets_true(create_event):
    """Toggle to published=True returns success=True and published=True."""
    event_id = create_event()

    req = DummyRequest(method="PATCH", json={"event_id": event_id, "published": True})
    resp, status = unwrap_response(location_api.admin_toggle_location_published(req))

    assert status == 200
    assert resp.get("success") is True
    assert resp.get("published") is True


@pytest.mark.integration
def test_toggle_location_publish_sets_false(create_event):
    """Toggle to published=False returns success=True and published=False."""
    event_id = create_event()

    req = DummyRequest(method="PATCH", json={"event_id": event_id, "published": False})
    resp, status = unwrap_response(location_api.admin_toggle_location_published(req))

    assert status == 200
    assert resp.get("success") is True
    assert resp.get("published") is False


@pytest.mark.integration
def test_toggle_location_nonexistent_event_returns_404():
    """Non-existent event_id returns 404."""
    req = DummyRequest(method="PATCH", json={"event_id": "ghost-event-id", "published": True})
    resp, status = unwrap_response(location_api.admin_toggle_location_published(req))

    assert status == 404


@pytest.mark.integration
def test_toggle_location_missing_fields_returns_400():
    """Missing published field returns 400."""
    req = DummyRequest(method="PATCH", json={"event_id": "any"})
    resp, status = unwrap_response(location_api.admin_toggle_location_published(req))

    assert status == 400


@pytest.mark.integration
def test_toggle_location_wrong_method_returns_405():
    """Non-PATCH request returns 405."""
    req = DummyRequest(method="GET", json={})
    resp, status = unwrap_response(location_api.admin_toggle_location_published(req))

    assert status == 405


# ---------------------------------------------------------------------------
# Full admin cycle: update → get → publish → get confirms published
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_admin_location_full_cycle(create_event):
    """Update location, retrieve it, then publish and confirm the flag is set."""
    event_id = create_event()

    # Update
    update_req = DummyRequest(method="PUT", json={
        "event_id": event_id,
        "label": "Cycle Hall",
        "address": "Via Ciclo 5, Roma",
        "maps_url": "https://maps.google.com/?q=cycle",
        "maps_embed_url": "",
        "message": "Accesso laterale",
    })
    _, update_status = unwrap_response(location_api.admin_update_event_location(update_req))
    assert update_status == 200

    # Get — fields must be saved, published still False
    get_req = DummyRequest(method="GET", args={"event_id": event_id})
    get_resp, get_status = unwrap_response(location_api.admin_get_event_location(get_req))
    assert get_status == 200
    assert get_resp.get("label") == "Cycle Hall"
    assert get_resp.get("address") == "Via Ciclo 5, Roma"
    assert get_resp.get("published") is False

    # Publish
    toggle_req = DummyRequest(method="PATCH", json={"event_id": event_id, "published": True})
    toggle_resp, toggle_status = unwrap_response(location_api.admin_toggle_location_published(toggle_req))
    assert toggle_status == 200
    assert toggle_resp.get("published") is True

    # Get again — published must now be True
    get_req2 = DummyRequest(method="GET", args={"event_id": event_id})
    get_resp2, _ = unwrap_response(location_api.admin_get_event_location(get_req2))
    assert get_resp2.get("published") is True
    assert get_resp2.get("label") == "Cycle Hall"


# ---------------------------------------------------------------------------
# send_location (participants_api)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_send_location_wrong_method_returns_405():
    """Non-POST request returns 405."""
    req = DummyRequest(method="GET", json={})
    resp, status = unwrap_response(participants_api.send_location(req))

    assert status == 405


@pytest.mark.integration
def test_send_location_missing_fields_returns_400():
    """Missing eventId/participantId returns 400."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(participants_api.send_location(req))

    assert status == 400


@pytest.mark.integration
def test_send_location_participant_not_found_returns_404(create_event):
    """Valid event but non-existent participant returns 404."""
    event_id = create_event()

    req = DummyRequest(method="POST", json={"eventId": event_id, "participantId": "ghost-participant"})
    resp, status = unwrap_response(participants_api.send_location(req))

    assert status == 404


# ---------------------------------------------------------------------------
# send_location_to_all (participants_api)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_send_location_to_all_creates_job(create_event):
    """POST with valid event_id returns 202 and a jobId."""
    event_id = create_event()

    req = DummyRequest(method="POST", json={"eventId": event_id})
    resp, status = unwrap_response(participants_api.send_location_to_all(req))

    assert status == 202
    job_id = resp.get("jobId")
    assert job_id

    # Cleanup job artifact
    try:
        db.collection("location_jobs").document(job_id).delete()
    except Exception:
        pass


@pytest.mark.integration
def test_send_location_to_all_nonexistent_event_returns_404():
    """Non-existent event returns 404."""
    req = DummyRequest(method="POST", json={"eventId": "ghost-event-id"})
    resp, status = unwrap_response(participants_api.send_location_to_all(req))

    assert status == 404


@pytest.mark.integration
def test_send_location_to_all_wrong_method_returns_405():
    """Non-POST request returns 405."""
    req = DummyRequest(method="GET", json={})
    resp, status = unwrap_response(participants_api.send_location_to_all(req))

    assert status == 405
