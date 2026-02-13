from types import SimpleNamespace

import pytest

from services import mail_service as mail_module
from services.mail_service import EmailAttachment, EmailMessage, GmailMailService, get_mail_config


def test_get_mail_config_reads_env(monkeypatch):
    """Reads Gmail config from environment variables."""
    monkeypatch.setenv("SCOPES", "scope1,scope2")
    monkeypatch.setenv("SERVICE_MAIL_FILE", "file.json")
    monkeypatch.setenv("USER_EMAIL", "user@example.com")
    monkeypatch.setenv("REFRESH_TOKEN", "refresh")
    monkeypatch.setenv("CLIENT_ID", "client")
    monkeypatch.setenv("CLIENT_SECRET", "secret")

    config = get_mail_config()

    assert config.scopes == ["scope1", "scope2"]
    assert config.user_email == "user@example.com"
    assert config.refresh_token == "refresh"
    assert config.client_id == "client"
    assert config.client_secret == "secret"


def test_build_plain_message_sets_headers():
    """Builds a plain MIME message with headers."""
    email = EmailMessage(
        to_email="to@example.com",
        subject="Subject",
        text_content="Hello",
    )
    msg = mail_module._build_plain_message(email, "from@example.com")
    assert msg["to"] == "to@example.com"
    assert msg["from"] == "from@example.com"
    assert msg["subject"] == "Subject"


def test_build_multipart_message_includes_attachment():
    """Builds multipart message when html/attachment is present."""
    email = EmailMessage(
        to_email="to@example.com",
        subject="Subject",
        text_content="Hello",
        html_content="<p>Hello</p>",
        attachment=EmailAttachment(content=b"data", filename="file.pdf"),
    )
    msg = mail_module._build_multipart_message(email, "from@example.com")
    assert msg["to"] == "to@example.com"
    assert msg["from"] == "from@example.com"
    assert msg["subject"] == "Subject"


def test_gmail_send_success(monkeypatch):
    """Sends email successfully via GmailMailService."""
    service = GmailMailService()
    monkeypatch.setattr(mail_module, "_build_gmail_service", lambda config: SimpleNamespace())
    monkeypatch.setattr(mail_module, "_encode_message", lambda message: "encoded")
    calls = {"sent": []}

    def fake_send(service_obj, raw_message):
        calls["sent"].append(raw_message)
        return True

    monkeypatch.setattr(mail_module, "_send_email_message", fake_send)
    monkeypatch.setenv("USER_EMAIL", "from@example.com")
    monkeypatch.setenv("REFRESH_TOKEN", "refresh")
    monkeypatch.setenv("CLIENT_ID", "client")
    monkeypatch.setenv("CLIENT_SECRET", "secret")

    email = EmailMessage(to_email="to@example.com", subject="Subject", text_content="Hello")
    assert service.send(email) is True
    assert calls["sent"] == ["encoded"]


def test_gmail_send_failure(monkeypatch):
    """Returns False when sending raises."""
    service = GmailMailService()
    monkeypatch.setattr(mail_module, "_build_gmail_service", lambda config: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setenv("USER_EMAIL", "from@example.com")
    monkeypatch.setenv("REFRESH_TOKEN", "refresh")
    monkeypatch.setenv("CLIENT_ID", "client")
    monkeypatch.setenv("CLIENT_SECRET", "secret")
    email = EmailMessage(to_email="to@example.com", subject="Subject", text_content="Hello")
    assert service.send(email) is False
