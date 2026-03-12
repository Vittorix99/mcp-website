import pytest

from services import mail_service as mail_module
from services.mail_service import EmailAttachment, EmailMessage, MailerSendMailService, get_mail_config


def test_get_mail_config_reads_env(monkeypatch):
    """Reads MailerSend config from environment variables."""
    monkeypatch.setenv("MAILERSEND_API_KEY", "api-key")
    monkeypatch.setenv("MAILERSEND_FROM_EMAIL", "user@example.com")
    monkeypatch.setenv("MAILERSEND_FROM_NAME", "MCP")
    monkeypatch.setenv("MAILERSEND_REPLY_TO", "reply@example.com")

    config = get_mail_config()

    assert config.api_key == "api-key"
    assert config.from_email == "user@example.com"
    assert config.from_name == "MCP"
    assert config.reply_to == "reply@example.com"


def test_mailersend_send_success(monkeypatch):
    """Sends email successfully via MailerSendMailService."""
    captured = {"builder": None, "sent": None}

    class FakeResponse:
        def __init__(self, success=True):
            self.success = success
            self.status_code = 202
            self.data = {}

    class FakeEmailSender:
        def send(self, request):
            captured["sent"] = request
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.emails = FakeEmailSender()

    class FakeBuilder:
        def __init__(self):
            self.data = {}
        def from_email(self, email, name=None):
            self.data["from"] = {"email": email, "name": name}
            return self
        def to_many(self, recipients):
            self.data["to"] = recipients
            return self
        def subject(self, subject):
            self.data["subject"] = subject
            return self
        def html(self, html):
            self.data["html"] = html
            return self
        def text(self, text):
            self.data["text"] = text
            return self
        def attach_file(self, path):
            self.data["attachment_path"] = path
            return self
        def build(self):
            return self.data

    monkeypatch.setattr(mail_module, "MailerSendClient", FakeClient)
    monkeypatch.setattr(mail_module, "EmailBuilder", FakeBuilder)
    monkeypatch.setenv("MAILERSEND_API_KEY", "api-key")
    monkeypatch.setenv("MAILERSEND_FROM_EMAIL", "from@example.com")
    monkeypatch.setenv("MAILERSEND_FROM_NAME", "Sender")
    monkeypatch.setenv("MAILERSEND_FROM_EMAIL_MEMBERSHIPS", "memberships@example.com")
    monkeypatch.setenv("MAILERSEND_FROM_NAME_MEMBERSHIPS", "Membership Desk")

    service = MailerSendMailService()
    email = EmailMessage(
        to_email="to@example.com",
        subject="Subject",
        text_content="Hello",
        html_content="<p>Hello</p>",
        attachment=EmailAttachment(content=b"data", filename="file.pdf"),
        category="memberships",
    )

    assert service.send(email) is True

    assert captured["api_key"] == "api-key"
    assert captured["sent"]["from"]["email"] == "memberships@example.com"
    assert captured["sent"]["from"]["name"] == "Membership Desk"
    assert captured["sent"]["to"] == [{"email": "to@example.com"}]
    assert captured["sent"]["subject"] == "Subject"
    assert captured["sent"]["html"] == "<p>Hello</p>"
    assert captured["sent"]["text"] == "Hello"
    assert "attachment_path" in captured["sent"]


def test_mailersend_send_failure(monkeypatch):
    """Returns False when HTTP error occurs."""
    class FakeResponse:
        def __init__(self):
            self.success = False
            self.status_code = 500
            self.data = {"message": "boom"}

    class FakeEmailSender:
        def send(self, request):
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            self.emails = FakeEmailSender()

    class FakeBuilder:
        def __init__(self): pass
        def from_email(self, *args, **kwargs): return self
        def to_many(self, *args, **kwargs): return self
        def subject(self, *args, **kwargs): return self
        def text(self, *args, **kwargs): return self
        def build(self): return {}

    monkeypatch.setattr(mail_module, "MailerSendClient", FakeClient)
    monkeypatch.setattr(mail_module, "EmailBuilder", FakeBuilder)
    monkeypatch.setenv("MAILERSEND_API_KEY", "api-key")
    monkeypatch.setenv("MAILERSEND_FROM_EMAIL", "from@example.com")

    service = MailerSendMailService()
    email = EmailMessage(to_email="to@example.com", subject="Subject", text_content="Hello")

    assert service.send(email) is False
