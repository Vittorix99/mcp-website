import pytest

from services.communications.mail_service import EmailMessage, mail_service
from tests.integration.gmail_utils import wait_for_message


@pytest.mark.integration
@pytest.mark.email
def test_mail_service_sends_real_email(gmail_service, unique_email, unique_subject):
    """Sends a real email via Gmail API and verifies it's visible in Sent."""
    ok = mail_service.send(
        EmailMessage(
            to_email=unique_email,
            subject=unique_subject,
            text_content="Integration test email",
        )
    )
    assert ok is True

    query = f'in:sent subject:"{unique_subject}" to:{unique_email}'
    assert wait_for_message(gmail_service, query)
