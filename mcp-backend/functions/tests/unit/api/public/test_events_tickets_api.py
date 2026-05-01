import types

from api.public import events_tickets_api
from dto.participant_api import CheckParticipantsResponseDTO
from errors.service_errors import ForbiddenError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_check_participants_invalid_method():
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(events_tickets_api.check_participants(req))
    assert status == 405
    assert resp["error"] == "Invalid method"


def test_check_participants_missing_payload():
    req = DummyRequest(method="POST", json={"participants": []})
    resp, status = unwrap_response(events_tickets_api.check_participants(req))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_check_participants_happy_path(monkeypatch):
    monkeypatch.setattr(
        events_tickets_api,
        "participants_service",
        types.SimpleNamespace(check_participants=lambda event_id, participants: CheckParticipantsResponseDTO(valid=True)),
    )

    req = DummyRequest(
        method="POST",
        json={"eventId": "evt-1", "participants": [{"email": "a@example.com"}]},
    )
    resp, status = unwrap_response(events_tickets_api.check_participants(req))
    assert status == 200
    assert resp["valid"] is True


def test_check_participants_validation_error_with_details(monkeypatch):
    class DetailedValidationError(ValidationError):
        def __init__(self):
            super().__init__("validation_error")
            self.details = ["duplicated participant"]

    monkeypatch.setattr(
        events_tickets_api,
        "participants_service",
        types.SimpleNamespace(
            check_participants=lambda *_args, **_kwargs: (_ for _ in ()).throw(DetailedValidationError())
        ),
    )

    req = DummyRequest(method="POST", json={"eventId": "evt-1", "participants": [{"email": "a@example.com"}]})
    resp, status = unwrap_response(events_tickets_api.check_participants(req))
    assert status == 400
    assert resp["error"] == "validation_error"
    assert resp["messages"] == ["duplicated participant"]


def test_check_participants_forbidden(monkeypatch):
    monkeypatch.setattr(
        events_tickets_api,
        "participants_service",
        types.SimpleNamespace(
            check_participants=lambda *_args, **_kwargs: (_ for _ in ()).throw(ForbiddenError("not allowed"))
        ),
    )

    req = DummyRequest(method="POST", json={"eventId": "evt-1", "participants": [{"email": "a@example.com"}]})
    resp, status = unwrap_response(events_tickets_api.check_participants(req))
    assert status == 403
    assert resp["error"] == "not allowed"
