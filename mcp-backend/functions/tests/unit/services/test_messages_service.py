import pytest

from dto import ContactMessageDTO
from services.messages_service import MessagesService
from services.service_errors import ExternalServiceError, NotFoundError, ValidationError


class _DummyMessageRepo:
    def __init__(self):
        self.messages = {}
        self.deleted = []
        self.updated = []
        self.created = []

    def list_ordered_by_name(self):
        return list(self.messages.values())

    def get(self, message_id):
        return self.messages.get(message_id)

    def delete(self, message_id):
        self.deleted.append(message_id)
        self.messages.pop(message_id, None)

    def update(self, message_id, payload):
        self.updated.append((message_id, payload))

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
    service.message_repository.messages["msg-1"] = ContactMessageDTO(
        id="msg-1", name="Mario", email="mario@example.com", message="Hi"
    )
    payload = service.get_all()
    assert payload == [{"id": "msg-1", "name": "Mario", "email": "mario@example.com", "message": "Hi", "answered": False}]


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
    service.message_repository.messages["msg-1"] = ContactMessageDTO(id="msg-1", name="Mario")
    payload = service.delete_by_id("msg-1")
    assert payload["deletedId"] == "msg-1"
    assert "msg-1" in service.message_repository.deleted


def test_reply_missing_fields():
    """Rejects reply when required fields are missing."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.reply("", "subject", "body", "msg-1")


def test_reply_send_failure(monkeypatch):
    """Raises when email send fails."""
    service = _make_service()
    monkeypatch.setattr("services.messages_service.mail_service.send", lambda *args, **kwargs: False)
    with pytest.raises(ExternalServiceError):
        service.reply("mario@example.com", "subject", "body", "msg-1")


def test_reply_happy_path(monkeypatch):
    """Sends reply and marks message as answered."""
    service = _make_service()
    monkeypatch.setattr("services.messages_service.mail_service.send", lambda *args, **kwargs: True)
    payload = service.reply("mario@example.com", "subject", "body", "msg-1")
    assert payload["emailSentTo"] == "mario@example.com"
    assert service.message_repository.updated


def test_submit_contact_message_missing_fields():
    """Rejects missing name/email/message."""
    service = _make_service()
    dto = ContactMessageDTO(name="Mario")
    with pytest.raises(ValidationError):
        service.submit_contact_message(dto)


def test_submit_contact_message_missing_destination(monkeypatch):
    """Rejects when destination email is missing."""
    service = _make_service()
    monkeypatch.delenv("USER_EMAIL", raising=False)
    dto = ContactMessageDTO(name="Mario", email="mario@example.com", message="Hi")
    with pytest.raises(ValidationError):
        service.submit_contact_message(dto)


def test_submit_contact_message_send_failure(monkeypatch):
    """Raises when sending contact message fails."""
    service = _make_service()
    monkeypatch.setenv("USER_EMAIL", "owner@example.com")
    monkeypatch.setattr("services.messages_service.mail_service.send", lambda *args, **kwargs: False)
    dto = ContactMessageDTO(name="Mario", email="mario@example.com", message="Hi")
    with pytest.raises(ExternalServiceError):
        service.submit_contact_message(dto)


def test_submit_contact_message_happy_path(monkeypatch):
    """Sends message and stores it."""
    service = _make_service()
    monkeypatch.setenv("USER_EMAIL", "owner@example.com")
    calls = {"sent": 0}

    def fake_send(*args, **kwargs):
        calls["sent"] += 1
        return True

    monkeypatch.setattr("services.messages_service.mail_service.send", fake_send)
    dto = ContactMessageDTO(name="Mario", email="mario@example.com", message="Hi")
    payload = service.submit_contact_message(dto)
    assert payload["message"]
    assert service.message_repository.created
    assert calls["sent"] == 1


def test_submit_contact_message_send_copy(monkeypatch):
    """Sends a copy when send_copy is True."""
    service = _make_service()
    monkeypatch.setenv("USER_EMAIL", "owner@example.com")
    calls = {"sent": 0}

    def fake_send(*args, **kwargs):
        calls["sent"] += 1
        return True

    monkeypatch.setattr("services.messages_service.mail_service.send", fake_send)
    dto = ContactMessageDTO(name="Mario", email="mario@example.com", message="Hi")
    service.submit_contact_message(dto, send_copy=True)
    assert calls["sent"] == 2
