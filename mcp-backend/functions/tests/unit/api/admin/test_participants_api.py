import types

from api.admin import participants_api
from services.service_errors import ExternalServiceError, NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_participants_by_event_invalid_method():
    """Rejects invalid method for list participants."""
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(participants_api.get_participants_by_event(req))
    assert status == 405


def test_get_participants_by_event_missing_event():
    """Returns 400 when eventId is missing."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(participants_api.get_participants_by_event(req))
    assert status == 400
    assert resp["error"] == "Missing eventId"


def test_get_participants_by_event_happy_path(monkeypatch):
    """Returns participants list for an event."""
    monkeypatch.setattr(
        participants_api,
        "participants_service",
        types.SimpleNamespace(get_all=lambda event_id: [{"id": "part-1"}]),
    )
    req = DummyRequest(method="POST", json={"eventId": "evt-1"})
    resp, status = unwrap_response(participants_api.get_participants_by_event(req))
    assert status == 200
    assert resp == [{"id": "part-1"}]


def test_get_participant_missing_params():
    """Returns 400 when participantId or eventId is missing."""
    req = DummyRequest(method="POST", json={"eventId": "evt-1"})
    resp, status = unwrap_response(participants_api.get_participant(req))
    assert status == 400
    assert resp["error"] == "Missing participantId or eventId"


def test_create_participant_missing_body():
    """Returns 400 when request body is missing."""
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(participants_api.create_participant(req))
    assert status == 400
    assert resp["error"] == "Missing participant data or event_id"


def test_create_participant_validation_error(monkeypatch):
    """Maps validation errors to 400."""
    monkeypatch.setattr(
        participants_api,
        "participants_service",
        types.SimpleNamespace(create=lambda data: (_ for _ in ()).throw(ValidationError("bad"))),
    )
    req = DummyRequest(method="POST", json={"event_id": "evt-1"})
    resp, status = unwrap_response(participants_api.create_participant(req))
    assert status == 400
    assert resp["error"] == "bad"


def test_update_participant_missing_params():
    """Returns 400 when participantId/event_id is missing."""
    req = DummyRequest(method="PUT", json={"event_id": "evt-1"})
    resp, status = unwrap_response(participants_api.update_participant(req))
    assert status == 400
    assert resp["error"] == "Missing participantId or event_id"


def test_delete_participant_missing_params():
    """Returns 400 when delete payload is incomplete."""
    req = DummyRequest(method="DELETE", json={"event_id": "evt-1"})
    resp, status = unwrap_response(participants_api.delete_participant(req))
    assert status == 400
    assert resp["error"] == "Missing participantId or event_id"


def test_send_ticket_missing_params():
    """Returns 400 when eventId/participantId is missing."""
    req = DummyRequest(method="POST", json={"eventId": "evt-1"})
    resp, status = unwrap_response(participants_api.send_ticket(req))
    assert status == 400
    assert resp["error"] == "Missing eventId or participantId"


def test_send_ticket_external_error(monkeypatch):
    """Maps ticket errors to 502."""
    monkeypatch.setattr(
        participants_api,
        "participants_service",
        types.SimpleNamespace(send_ticket=lambda *args, **kwargs: (_ for _ in ()).throw(ExternalServiceError("boom"))),
    )
    req = DummyRequest(method="POST", json={"eventId": "evt-1", "participantId": "part-1"})
    resp, status = unwrap_response(participants_api.send_ticket(req))
    assert status == 502
    assert resp["error"] == "boom"


def test_get_participant_not_found(monkeypatch):
    """Maps not found errors to 404."""
    monkeypatch.setattr(
        participants_api,
        "participants_service",
        types.SimpleNamespace(get_by_id=lambda *args, **kwargs: (_ for _ in ()).throw(NotFoundError("missing"))),
    )
    req = DummyRequest(method="POST", json={"eventId": "evt-1", "participantId": "part-1"})
    resp, status = unwrap_response(participants_api.get_participant(req))
    assert status == 404
    assert resp["error"] == "missing"
