import types

from api.admin import events_api
from services.service_errors import ConflictError, NotFoundError, ServiceError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_admin_create_event_happy_path(monkeypatch):
    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(create_event=lambda dto, admin_uid: {"eventId": "evt-1"}),
    )
    req = DummyRequest(
        method="POST",
        json={
            "title": "Test",
            "location": "Milano",
            "locationHint": "Ingresso A",
            "date": "13-02-2026",
            "startTime": "20:00",
        },
    )
    resp, status = unwrap_response(events_api.admin_create_event(req))
    assert status == 201
    assert resp["eventId"] == "evt-1"


def test_admin_create_event_missing_body():
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(events_api.admin_create_event(req))
    assert status == 400
    assert resp["error"] == "Missing request body"


def test_admin_create_event_validation_error():
    req = DummyRequest(
        method="POST",
        json={"title": "Test"},
    )
    resp, status = unwrap_response(events_api.admin_create_event(req))
    assert status == 400
    assert resp["error"] == "validation_error"


def test_admin_create_event_service_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise ValidationError("boom")

    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(create_event=raise_error),
    )
    req = DummyRequest(
        method="POST",
        json={
            "title": "Test",
            "location": "Milano",
            "locationHint": "Ingresso A",
            "date": "13-02-2026",
            "startTime": "20:00",
        },
    )
    resp, status = unwrap_response(events_api.admin_create_event(req))
    assert status == 400
    assert resp["error"] == "boom"


def test_admin_update_event_invalid_method():
    req = DummyRequest(
        method="GET",
        json={"id": "evt-1", "title": "Test"},
    )
    resp, status = unwrap_response(events_api.admin_update_event(req))
    assert status == 405


def test_admin_update_event_missing_id():
    req = DummyRequest(
        method="PUT",
        json={"title": "Test"},
    )
    resp, status = unwrap_response(events_api.admin_update_event(req))
    assert status == 400
    assert resp["error"] == "validation_error"


def test_admin_update_event_not_found(monkeypatch):
    def raise_error(*args, **kwargs):
        raise NotFoundError("missing")

    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(update_event=raise_error),
    )
    req = DummyRequest(
        method="PUT",
        json={"id": "evt-1", "title": "Test"},
    )
    resp, status = unwrap_response(events_api.admin_update_event(req))
    assert status == 404
    assert resp["error"] == "missing"


def test_admin_delete_event_invalid_method():
    req = DummyRequest(method="GET", json={"id": "evt-1"})
    resp, status = unwrap_response(events_api.admin_delete_event(req))
    assert status == 405


def test_admin_get_event_by_id_missing():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(events_api.admin_get_event_by_id(req))
    assert status == 400
    assert resp["error"] == "Missing event ID or slug"


def test_admin_get_all_events_happy_path(monkeypatch):
    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(get_all_events=lambda: [{"id": "evt-1"}]),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(events_api.admin_get_all_events(req))
    assert status == 200
    assert resp == [{"id": "evt-1"}]


def test_admin_get_event_by_id_conflict_mapping(monkeypatch):
    def raise_error(*args, **kwargs):
        raise ConflictError("conflict")

    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(get_event_by_id=raise_error),
    )
    req = DummyRequest(method="GET", args={"id": "evt-1"})
    resp, status = unwrap_response(events_api.admin_get_event_by_id(req))
    assert status == 409
    assert resp["error"] == "conflict"


def test_admin_get_event_by_id_service_error_mapping(monkeypatch):
    def raise_error(*args, **kwargs):
        raise ServiceError("boom")

    monkeypatch.setattr(
        events_api,
        "events_service",
        types.SimpleNamespace(get_event_by_id=raise_error),
    )
    req = DummyRequest(method="GET", args={"id": "evt-1"})
    resp, status = unwrap_response(events_api.admin_get_event_by_id(req))
    assert status == 500
    assert resp["error"] == "boom"
