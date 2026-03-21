import logging
import os

from google.cloud import firestore

from dto import ContactMessageDTO
from models import ContactMessage
from repositories.message_repository import MessageRepository
from services.communications.mail_service import EmailMessage, mail_service
from errors.service_errors import ExternalServiceError, NotFoundError, ValidationError

logger = logging.getLogger("MessagesService")


def _resolve_contact_destination_email() -> str:
    """
    Resolve admin destination for contact form messages with provider-agnostic env names.
    Keeps legacy envs as fallback for backward compatibility.
    """
    to_email = (
        os.environ.get("CONTACT_MESSAGES_TO_EMAIL")
        or os.environ.get("MAIL_DESTINATION_EMAIL")
        or os.environ.get("MAILERSEND_FROM_EMAIL")
        or os.environ.get("USER_EMAIL")
        or os.environ.get("GMAIL_MAIL")
    )
    return (to_email or "").strip()


class MessagesService:
    def __init__(self):
        self.message_repository = MessageRepository()
        self.logger = logger

    def get_all(self):
        self.logger.debug("Fetching all contact messages from Firestore.")
        messages = self.message_repository.list_ordered_by_name()
        result = [message.to_payload() for message in messages]
        self.logger.debug("Found %s messages.", len(result))
        return result

    def delete_by_id(self, message_id: str):
        self.logger.debug("Deleting contact message with ID: %s", message_id)
        if not message_id:
            raise ValidationError("Message ID is required")
        existing = self.message_repository.get(message_id)
        if not existing:
            raise NotFoundError("Message not found")
        self.message_repository.delete(message_id)
        return {"success": True, "deletedId": message_id}

    def reply(self, to: str, subject: str, body: str, message_id: str):
        self.logger.debug("Sending email reply to: %s, subject: %s", to, subject)

        if not to or not body or not message_id:
            raise ValidationError("Missing required fields")

        sent = mail_service.send(
            EmailMessage(
                to_email=to,
                subject=subject or "Risposta al tuo messaggio",
                text_content=body,
                category="communication",
            )
        )
        if not sent:
            raise ExternalServiceError("Failed to send reply email")

        self.message_repository.update(message_id, ContactMessageDTO(answered=True))
        self.logger.info("Marked message %s as answered", message_id)
        return {"success": True, "emailSentTo": to}

    def submit_contact_message(self, dto: ContactMessageDTO, send_copy: bool = False):
        if not dto.name or not dto.email or not dto.message:
            raise ValidationError("Missing required fields")

        to_email = _resolve_contact_destination_email()
        if not to_email:
            raise ValidationError("Missing destination email")

        subject = f"Contact Us Form Submission from {dto.name}"
        admin_body = (
            "Nuovo messaggio ricevuto dal form Contact Us.\n\n"
            f"Nome e cognome: {dto.name}\n"
            f"Email: {dto.email}\n\n"
            f"Messaggio:\n{dto.message}"
        )

        sent = mail_service.send(
            EmailMessage(
                to_email=to_email,
                subject=subject,
                text_content=admin_body,
                category="communication",
            )
        )
        if not sent:
            raise ExternalServiceError("Failed to send message")

        message = ContactMessage(
            name=dto.name,
            email=dto.email,
            message=dto.message,
            answered=False,
            subject=dto.subject,
            participant_id=dto.participant_id,
            event_id=dto.event_id,
            error_message=dto.error_message,
            timestamp=firestore.SERVER_TIMESTAMP,
        )
        doc_id = self.message_repository.create_from_model(message)
        self.logger.info("Contact message stored with id %s", doc_id)

        if send_copy:
            copy_body = (
                "Abbiamo ricevuto il tuo messaggio dal form Contact Us.\n\n"
                f"Nome e cognome: {dto.name}\n"
                f"Email: {dto.email}\n\n"
                f"Messaggio inviato:\n{dto.message}"
            )
            mail_service.send(
                EmailMessage(
                    to_email=dto.email,
                    subject="Copia del tuo messaggio",
                    text_content=copy_body,
                    category="communication",
                )
            )
        return {"message": "Message sent successfully"}
