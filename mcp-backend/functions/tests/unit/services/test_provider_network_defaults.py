import importlib

import pytest

from config.runtime_settings import RuntimeConfigurationError, load_runtime_settings
from tests.config_fixtures import cloud_environment


def test_local_mail_and_imported_proxy_are_offline(monkeypatch):
    module = importlib.import_module("services.communications.mail_service")
    early_reference = module.mail_service
    fake = module.build_mail_service(load_runtime_settings({"MCP_ENV": "test"}))
    monkeypatch.setattr(module, "_mail_service", fake)
    message = module.EmailMessage(to_email="recipient@example.test", subject="Test", text_content="Fixture")
    assert early_reference.send(message) is True
    assert fake.sent_messages == [message]


def test_sender_key_and_enabled_flag_do_not_bypass_local_policy(monkeypatch):
    from services.sender.sender_service import SenderService
    settings = load_runtime_settings({"MCP_ENV": "test", "SENDER_API_KEY": "sentinel"})
    service = SenderService(api_key="sentinel", enabled=True, settings=settings)
    assert service.enabled is False
    assert service.list_groups() is None


def test_staging_mail_is_disabled_by_default():
    module = importlib.import_module("services.communications.mail_service")
    service = module.build_mail_service(load_runtime_settings(cloud_environment("staging")))
    message = module.EmailMessage(to_email="customer@example.test", subject="Test", text_content="Fixture")
    assert service.send(message) is False


@pytest.mark.parametrize("recipient", ["customer@other.example.test", "customer@other.example.test,owned@staging.example.test"])
def test_staging_mail_recipient_allowlist_blocks_before_transport(monkeypatch, recipient):
    module = importlib.import_module("services.communications.mail_service")
    settings = load_runtime_settings({**cloud_environment("staging"), "MAIL_MODE": "staging",
        "MAIL_ALLOWED_RECIPIENTS": "test@example.test,@staging.example.test",
        "MAILERSEND_API_KEY": "sentinel", "MAILERSEND_FROM_EMAIL": "sender@staging.example.test"})
    service = module.build_mail_service(settings)
    monkeypatch.setattr(module.MailerSendRoutes, "send_email", lambda *a, **k: pytest.fail("Transport reached"))
    assert service.send(module.EmailMessage(to_email=recipient, subject="Test", text_content="Fixture")) is False
