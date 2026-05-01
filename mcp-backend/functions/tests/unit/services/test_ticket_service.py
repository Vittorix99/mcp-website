from io import BytesIO
from types import SimpleNamespace

import pytest

from models import Event, EventParticipant
from services.events.ticket_service import TicketService, TicketDocument


class _DummyDocsService:
    def __init__(self, document=None):
        self.document = document or SimpleNamespace(
            storage_path="tickets/test.pdf",
            public_url="https://example.com/ticket.pdf",
            buffer=BytesIO(b"pdf"),
        )
        self.calls = []

    def create_ticket_document(self, participant_payload, event_payload, storage_path, logo_path=None):
        self.calls.append((participant_payload, event_payload, storage_path))
        return self.document


class _DummyEventRepo:
    def __init__(self, model=None):
        self.model = model

    def get_model(self, event_id):
        return self.model


class _DummyParticipantRepo:
    def __init__(self):
        self.updated = []

    def update_from_model(self, event_id, participant_id, participant):
        self.updated.append((event_id, participant_id, participant))


class _DummyMessageRepo:
    def __init__(self):
        self.created = []

    def create_from_model(self, message):
        self.created.append(message)
        return "message-1"


def _make_service():
    service = TicketService(
        documents_service=_DummyDocsService(),
        event_repository=_DummyEventRepo(),
        participant_repository=_DummyParticipantRepo(),
        message_repository=_DummyMessageRepo(),
    )
    return service


def _participant(event_id="evt-1", email="mario@example.com"):
    return EventParticipant(
        event_id=event_id,
        name="Mario",
        surname="Rossi",
        email=email,
        phone="+390000000000",
        birthdate="01-01-1990",
    )


def test_create_ticket_document_builds_storage_path():
    """Builds a storage path when none is provided."""
    service = _make_service()
    participant = _participant()
    event = Event(title="Event Title")
    doc = service.create_ticket_document(participant, event)
    assert isinstance(doc, TicketDocument)
    assert doc.storage_path.startswith("tickets/")


def test_process_new_ticket_missing_event_id():
    """Returns error when participant has no event_id."""
    service = _make_service()
    participant = _participant(event_id="")
    result = service.process_new_ticket("part-1", participant)
    assert result["success"] is False
    assert "Missing event_id" in result["error"]


def test_process_new_ticket_event_not_found():
    """Returns error when event does not exist."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=None)
    result = service.process_new_ticket("part-1", _participant())
    assert result["success"] is False
    assert "not found" in result["error"]


def test_process_new_ticket_missing_email():
    """Returns error when participant email is missing."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    result = service.process_new_ticket("part-1", _participant(email=""), send=True)
    assert result["success"] is False
    assert "Missing participant email" in result["error"]


def test_process_new_ticket_send_failure(monkeypatch):
    """Returns error when mail send fails."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    monkeypatch.setattr("services.events.ticket_service.mail_service.send", lambda *args, **kwargs: False)
    result = service.process_new_ticket("part-1", _participant(), send=True)
    assert result["success"] is False
    assert "Failed to send email" in result["error"]


def test_process_new_ticket_happy_path(monkeypatch):
    """Sends ticket and updates participant."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    monkeypatch.setattr("services.events.ticket_service.mail_service.send", lambda *args, **kwargs: True)
    result = service.process_new_ticket("part-1", _participant(), send=True)
    assert result["success"] is True
    assert service.participant_repository.updated


def test_process_new_ticket_attachment_filename(monkeypatch):
    """Uses event title in attachment filename for outbound ticket emails."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="MCP Spring 2026!", date="13-02-2026"))
    captured = {}

    def fake_send(email_message):
        captured["message"] = email_message
        return True

    monkeypatch.setattr("services.events.ticket_service.mail_service.send", fake_send)
    result = service.process_new_ticket("part-1", _participant(), send=True)
    assert result["success"] is True
    assert captured["message"].attachment is not None
    assert captured["message"].attachment.filename == "mcp_spring_2026_participation.pdf"
    assert "allegata a questa email" in (captured["message"].html_content or "")
    assert "Scarica la tua partecipazione" not in (captured["message"].html_content or "")


def test_process_new_ticket_no_send(monkeypatch):
    """Creates ticket without sending email when send=False."""
    service = _make_service()
    service.event_repository = _DummyEventRepo(model=Event(title="Test", date="13-02-2026"))
    result = service.process_new_ticket("part-1", _participant(), send=False)
    assert result["success"] is True
    assert service.participant_repository.updated


def test_log_failed_ticket_email():
    """Logs failed ticket email to contact_message."""
    service = _make_service()
    service.log_failed_ticket_email("part-1", _participant(), "boom")
    assert len(service.message_repository.created) == 1
