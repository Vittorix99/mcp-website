import logging
import os
from typing import Optional

from google.cloud import firestore

from dto.message_api import (
    ContactFormRequestDTO,
    ContactMessageResponseDTO,
    MessageActionResponseDTO,
    ReplyMessageRequestDTO,
)
from interfaces.repositories import MessageRepositoryProtocol
from mappers.message_mappers import contact_form_dto_to_model, contact_message_to_response
from repositories.message_repository import MessageRepository
from services.communications.mail_service import EmailMessage, MailService, mail_service
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
    def __init__(
        self,
        message_repository: Optional[MessageRepositoryProtocol] = None,
        mail_service_instance: Optional[MailService] = None,
    ):
        self.message_repository = message_repository or MessageRepository()
        self.mail_service = mail_service_instance or mail_service
        self.logger = logger

    def get_all(self) -> list[ContactMessageResponseDTO]:
        self.logger.debug("Fetching all contact messages from Firestore.")
        messages = self.message_repository.list_models_ordered_by_name()
        result = [contact_message_to_response(message) for message in messages]
        self.logger.debug("Found %s messages.", len(result))
        return result

    def delete_by_id(self, message_id: str) -> MessageActionResponseDTO:
        self.logger.debug("Deleting contact message with ID: %s", message_id)
        if not message_id:
            raise ValidationError("Message ID is required")
        existing = self.message_repository.get_model(message_id)
        if not existing:
            raise NotFoundError("Message not found")
        self.message_repository.delete(message_id)
        return MessageActionResponseDTO(success=True, deletedId=message_id)

    def reply(self, dto: ReplyMessageRequestDTO) -> MessageActionResponseDTO:
        self.logger.debug("Sending email reply to: %s, subject: %s", dto.email, dto.subject)

        message = self.message_repository.get_model(dto.message_id)
        if not message:
            raise NotFoundError("Message not found")

        sent = self.mail_service.send(
            EmailMessage(
                to_email=str(dto.email),
                subject=dto.subject or "Risposta al tuo messaggio",
                text_content=dto.body,
                category="communication",
            )
        )
        if not sent:
            raise ExternalServiceError("Failed to send reply email")

        message.answered = True
        self.message_repository.update_from_model(dto.message_id, message)
        self.logger.info("Marked message %s as answered", dto.message_id)
        return MessageActionResponseDTO(success=True, emailSentTo=str(dto.email))

    def submit_contact_message(self, dto: ContactFormRequestDTO) -> MessageActionResponseDTO:
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

        sent = self.mail_service.send(
            EmailMessage(
                to_email=to_email,
                subject=subject,
                text_content=admin_body,
                category="communication",
            )
        )
        if not sent:
            raise ExternalServiceError("Failed to send message")

        message = contact_form_dto_to_model(
            dto,
            timestamp=firestore.SERVER_TIMESTAMP,
        )
        doc_id = self.message_repository.create_from_model(message)
        self.logger.info("Contact message stored with id %s", doc_id)

        if dto.send_copy:
            copy_body = (
                "Abbiamo ricevuto il tuo messaggio dal form Contact Us.\n\n"
                f"Nome e cognome: {dto.name}\n"
                f"Email: {dto.email}\n\n"
                f"Messaggio inviato:\n{dto.message}"
            )
            self.mail_service.send(
                EmailMessage(
                    to_email=str(dto.email),
                    subject="Copia del tuo messaggio",
                    text_content=copy_body,
                    category="communication",
                )
        )
        return MessageActionResponseDTO(message="Message sent successfully", success=True)
