from uuid import uuid4

import pytest

from config.firebase_config import db
from dto.message_api import ContactFormRequestDTO
from google.cloud.firestore_v1 import FieldFilter
from services.communications.messages_service import MessagesService


@pytest.mark.integration
@pytest.mark.email
@pytest.mark.usefixtures("mailersend_api_key")
def test_messages_service_sends_email_and_persists(unique_email):
    """Sends a real email and persists the contact message in Firestore."""
    service = MessagesService()
    suffix = uuid4().hex[:8]
    name = f"Integration User {suffix}"
    message_text = f"Integ message {suffix}"
    dto = ContactFormRequestDTO(
        name=name,
        email=unique_email,
        message=message_text,
        subject="Integration contact",
        send_copy=True,
    )

    doc_id = None
    try:
        result = service.submit_contact_message(dto)
        assert result.message == "Message sent successfully"

        docs = (
            db.collection("contact_message")
            .where(filter=FieldFilter("email", "==", unique_email))
            .where(filter=FieldFilter("message", "==", message_text))
            .limit(1)
            .get()
        )
        assert docs
        doc_id = docs[0].id
    finally:
        if doc_id:
            db.collection("contact_message").document(doc_id).delete()
