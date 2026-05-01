import types

from api.public import events_api
from dto.event_api import PublicEventResponseDTO
from errors.service_errors import NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_all_events_with_view(monkeypatch):
    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(
            list_public_events=lambda: [
                PublicEventResponseDTO(id="evt-1", slug="evt-1", title="Test", date="13-02-2026")
            ]
        ),
    )
    req = DummyRequest(method="GET", args={"view": "ids"})
    resp, status = unwrap_response(events_api.get_all_events(req))
    assert status == 200
    assert resp == [{"id": "evt-1", "slug": "evt-1"}]


def test_get_all_events_sanitized(monkeypatch):
    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(
            list_public_events=lambda: [
                PublicEventResponseDTO(id="evt-1", title="Test", date="13-02-2026")
            ]
        ),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(events_api.get_all_events(req))
    assert status == 200
    assert resp[0]["id"] == "evt-1"
    assert resp[0]["title"] == "Test"
    assert "participantsCount" not in resp[0]


def test_get_event_by_id_missing_params():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(events_api.get_event_by_id(req))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_get_event_by_id_not_found(monkeypatch):
    def raise_error(*args, **kwargs):
        raise NotFoundError("not found")

    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(get_public_event_by_id=raise_error),
    )
    req = DummyRequest(method="GET", args={"id": "evt-1"})
    resp, status = unwrap_response(events_api.get_event_by_id(req))
    assert status == 404
    assert resp["error"] == "not found"


def test_get_next_event_validation_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise ValidationError("bad")

    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(get_next_public_event=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(events_api.get_next_event(req))
    assert status == 400
    assert resp["error"] == "bad"
