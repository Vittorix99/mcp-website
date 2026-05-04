import pytest

from dto.message_api import ContactFormRequestDTO, ReplyMessageRequestDTO
from models import ContactMessage
from services.communications.messages_service import MessagesService
from errors.service_errors import ExternalServiceError, NotFoundError, ValidationError


class _DummyMessageRepo:
    def __init__(self):
        self.messages = {}
        self.deleted = []
        self.updated = []
        self.created = []

    def list_models_ordered_by_name(self):
        return list(self.messages.values())

    def get_model(self, message_id):
        return self.messages.get(message_id)

    def delete(self, message_id):
        self.deleted.append(message_id)
        self.messages.pop(message_id, None)

    def update_from_model(self, message_id, message):
        self.updated.append((message_id, message))

    def create_from_model(self, payload):
        self.created.append(payload)
        return "msg-1"


def _make_service():
    service = MessagesService()
    service.message_repository = _DummyMessageRepo()
    return service


def test_get_all_messages():
    """Returns serialized messages list."""
    service = _make_service()
    message = ContactMessage(name="Mario", email="mario@example.com", message="Hi")
    message.id = "msg-1"
    service.message_repository.messages["msg-1"] = message
    payload = service.get_all()
    assert payload[0].to_payload() == {"id": "msg-1", "name": "Mario", "email": "mario@example.com", "message": "Hi", "answered": False}


def test_delete_requires_id():
    """Rejects delete without message_id."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.delete_by_id("")


def test_delete_not_found():
    """Raises when message is missing."""
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.delete_by_id("msg-1")


def test_delete_happy_path():
    """Deletes an existing message."""
    service = _make_service()
    message = ContactMessage(name="Mario")
    message.id = "msg-1"
    service.message_repository.messages["msg-1"] = message
    payload = service.delete_by_id("msg-1")
    assert payload.deleted_id == "msg-1"
    assert "msg-1" in service.message_repository.deleted


def test_reply_missing_fields():
    """Rejects reply when required fields are missing."""
    with pytest.raises(Exception):
        ReplyMessageRequestDTO.model_validate({"email": "", "subject": "subject", "body": "body", "message_id": "msg-1"})


def test_reply_send_failure(monkeypatch):
    """Raises when email send fails."""
    service = _make_service()
    monkeypatch.setattr("services.communications.messages_service.mail_service.send", lambda *args, **kwargs: False)
    with pytest.raises(ExternalServiceError):
        service.message_repository.messages["msg-1"] = ContactMessage(email="mario@example.com")
        service.reply(ReplyMessageRequestDTO(email="mario@example.com", subject="subject", body="body", message_id="msg-1"))


def test_reply_happy_path(monkeypatch):
    """Sends reply and marks message as answered."""
    service = _make_service()
    monkeypatch.setattr("services.communications.messages_service.mail_service.send", lambda *args, **kwargs: True)
    service.message_repository.messages["msg-1"] = ContactMessage(email="mario@example.com")
    payload = service.reply(ReplyMessageRequestDTO(email="mario@example.com", subject="subject", body="body", message_id="msg-1"))
    assert payload.email_sent_to == "mario@example.com"
    assert service.message_repository.updated


def test_submit_contact_message_missing_fields():
    """Rejects missing name/email/message."""
    with pytest.raises(Exception):
        ContactFormRequestDTO.model_validate({"name": "Mario"})


def test_submit_contact_message_missing_destination(monkeypatch):
    """Rejects when destination email is missing."""
    service = _make_service()
    monkeypatch.delenv("CONTACT_MESSAGES_TO_EMAIL", raising=False)
    monkeypatch.delenv("MAIL_DESTINATION_EMAIL", raising=False)
    monkeypatch.delenv("MAILERSEND_FROM_EMAIL", raising=False)
    monkeypatch.delenv("USER_EMAIL", raising=False)
    monkeypatch.delenv("GMAIL_MAIL", raising=False)
    dto = ContactFormRequestDTO(name="Mario", email="mario@example.com", message="Hi")
    with pytest.raises(ValidationError):
        service.submit_contact_message(dto)


def test_submit_contact_message_send_failure(monkeypatch):
    """Raises when sending contact message fails."""
    service = _make_service()
    monkeypatch.setenv("CONTACT_MESSAGES_TO_EMAIL", "owner@example.com")
    monkeypatch.setattr("services.communications.messages_service.mail_service.send", lambda *args, **kwargs: False)
    dto = ContactFormRequestDTO(name="Mario", email="mario@example.com", message="Hi")
    with pytest.raises(ExternalServiceError):
        service.submit_contact_message(dto)


def test_submit_contact_message_happy_path(monkeypatch):
    """Sends message and stores it."""
    service = _make_service()
    monkeypatch.setenv("CONTACT_MESSAGES_TO_EMAIL", "owner@example.com")
    calls = {"sent": 0}

    def fake_send(*args, **kwargs):
        calls["sent"] += 1
        return True

    monkeypatch.setattr("services.communications.messages_service.mail_service.send", fake_send)
    dto = ContactFormRequestDTO(name="Mario", email="mario@example.com", message="Hi")
    payload = service.submit_contact_message(dto)
    assert payload.message
    assert service.message_repository.created
    assert calls["sent"] == 1


def test_submit_contact_message_send_copy(monkeypatch):
    """Sends a copy when send_copy is True."""
    service = _make_service()
    monkeypatch.setenv("CONTACT_MESSAGES_TO_EMAIL", "owner@example.com")
    calls = {"sent": 0}

    def fake_send(*args, **kwargs):
        calls["sent"] += 1
        return True

    monkeypatch.setattr("services.communications.messages_service.mail_service.send", fake_send)
    dto = ContactFormRequestDTO(name="Mario", email="mario@example.com", message="Hi", send_copy=True)
    service.submit_contact_message(dto)
    assert calls["sent"] == 2
