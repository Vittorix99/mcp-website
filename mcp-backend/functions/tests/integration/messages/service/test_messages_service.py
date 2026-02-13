from uuid import uuid4

import pytest

from config.firebase_config import db
from dto import ContactMessageDTO
from services.messages_service import MessagesService
from tests.integration.gmail_utils import wait_for_message


@pytest.mark.integration
@pytest.mark.email
def test_messages_service_sends_email_and_persists(gmail_service, unique_email):
    """Sends a real email and persists the contact message in Firestore."""
    service = MessagesService()
    suffix = uuid4().hex[:8]
    name = f"Integration User {suffix}"
    message_text = f"Integ message {suffix}"
    dto = ContactMessageDTO(
        name=name,
        email=unique_email,
        message=message_text,
        subject="Integration contact",
    )

    result = service.submit_contact_message(dto, send_copy=True)
    assert result.get("message") == "Message sent successfully"

    docs = (
        db.collection("contact_message")
        .where("email", "==", unique_email)
        .where("message", "==", message_text)
        .limit(1)
        .get()
    )
    assert docs
    doc_id = docs[0].id

    main_subject = f"Contact Us Form Submission from {name}"
    assert wait_for_message(gmail_service, f'in:sent subject:"{main_subject}"')
    assert wait_for_message(
        gmail_service,
        f'in:sent subject:"Copia del tuo messaggio" to:{unique_email}',
    )

    db.collection("contact_message").document(doc_id).delete()
