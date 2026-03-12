import pytest

from services.mail_service import EmailMessage, mail_service


@pytest.mark.integration
@pytest.mark.email
def test_mailersend_send_email(mailersend_api_key, unique_email, unique_subject):
    """Sends a real email via MailerSend API through mail_service."""
    ok = mail_service.send(
        EmailMessage(
            to_email=unique_email,
            subject=unique_subject,
            text_content="Mailersend integration test email",
        )
    )
    assert ok is True
