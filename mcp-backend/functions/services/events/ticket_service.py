import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, Optional

from google.cloud import firestore

from interfaces.repositories import EventRepositoryProtocol, MessageRepositoryProtocol, ParticipantRepositoryProtocol
from interfaces.services import DocumentsServiceProtocol
from models import ContactMessage, Event, EventParticipant
from repositories.event_repository import EventRepository
from repositories.message_repository import MessageRepository
from repositories.participant_repository import ParticipantRepository
from services.events.documents_service import DocumentsService
from services.communications.mail_service import EmailAttachment, EmailMessage, MailService, mail_service
from utils.templates_mail import get_ticket_email_template, get_ticket_email_text
from utils.safe_logging import redact_sensitive


@dataclass
class TicketDocument:
    storage_path: str
    public_url: str
    buffer: Optional[BytesIO] = None


class TicketService:
    def __init__(
        self,
        documents_service: Optional[DocumentsServiceProtocol] = None,
        event_repository: Optional[EventRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        message_repository: Optional[MessageRepositoryProtocol] = None,
        mail_service_instance: Optional[MailService] = None,
    ):
        self.logger = logging.getLogger("TicketService")
        self.documents_service = documents_service or DocumentsService()
        self.event_repository = event_repository or EventRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.message_repository = message_repository or MessageRepository()
        self.mail_service = mail_service_instance or mail_service

    def _normalize_participant(self, payload: Any) -> EventParticipant:
        if isinstance(payload, EventParticipant):
            return payload
        if isinstance(payload, dict):
            return EventParticipant.from_firestore(payload, doc_id=None)
        raise ValueError("participant_data must be an EventParticipant or dict")

    @staticmethod
    def _participant_payload(participant: EventParticipant) -> Dict[str, Any]:
        return {
            "id": participant.id,
            "name": participant.name,
            "surname": participant.surname,
            "email": participant.email,
            "phone": participant.phone,
            "membershipId": participant.membership_id,
            "entered": participant.entered,
            "ticket_pdf_url": participant.ticket_pdf_url,
            "ticket_sent": participant.ticket_sent,
            "price": participant.price,
            "riduzione": participant.riduzione,
        }

    @staticmethod
    def _event_payload(event: Event) -> Dict[str, Any]:
        return {
            "id": event.id,
            "title": event.title,
            "date": event.date,
            "startTime": event.start_time,
            "endTime": event.end_time,
            "locationHint": event.location_hint,
            "image": event.image,
            "type": event.purchase_mode.value if event.purchase_mode else None,
        }

    def _normalize_event_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, Event):
            return self._event_payload(payload)
        if isinstance(payload, dict):
            return dict(payload)
        raise ValueError("event_data must be an Event or dict")

    def _build_storage_path(
        self,
        event_title: Optional[str],
        name: Optional[str],
        surname: Optional[str],
    ) -> str:
        safe_title = (event_title or "event").strip() or "event"
        safe_name = (name or "user").strip() or "user"
        safe_surname = (surname or "").strip()
        name_surname = f"{safe_name}_{safe_surname}".strip("_")
        return f"tickets/{safe_title}/{name_surname}_ticket.pdf"

    def _build_attachment_filename(self, event_title: Optional[str]) -> str:
        raw_title = (event_title or "").strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", raw_title).strip("_")
        if not normalized:
            normalized = "event"
        return f"{normalized}_participation.pdf"

    def create_ticket_document(
        self,
        participant_data: Any,
        event_data: Any,
        storage_path: Optional[str] = None,
    ) -> TicketDocument:
        participant = self._normalize_participant(participant_data)
        participant_payload = self._participant_payload(participant)
        event_payload = self._normalize_event_payload(event_data)

        if storage_path is None:
            storage_path = self._build_storage_path(
                event_payload.get("title"),
                participant_payload.get("name"),
                participant_payload.get("surname"),
            )

        document = self.documents_service.create_ticket_document(
            participant_payload,
            event_payload,
            storage_path,
        )
        return TicketDocument(
            storage_path=document.storage_path,
            public_url=document.public_url,
            buffer=document.buffer,
        )

    def process_new_ticket(self, participant_id: str, participant_data: Any, send: bool = True) -> Dict[str, Any]:
        try:
            participant = self._normalize_participant(participant_data)
            event_id = participant.event_id
            if not event_id:
                self.logger.warning("Missing event_id")
                return {"success": False, "error": "Missing event_id"}

            event_model = self.event_repository.get_model(event_id)
            if not event_model:
                return {"success": False, "error": f"Event {event_id} not found"}
            event_payload = self._event_payload(event_model)

            document = self.create_ticket_document(participant, event_payload)
            participant.ticket_pdf_url = document.public_url
            participant.ticket_sent = False

            if send:
                if not participant.email:
                    return {"success": False, "error": "Missing participant email"}
                ticket_payload = self._participant_payload(participant)
                subject = f"La tua partecipazione per {event_payload.get('title')}"
                attachment = None
                if document.buffer:
                    attachment = EmailAttachment(
                        content=document.buffer.getvalue(),
                        filename=self._build_attachment_filename(event_payload.get("title")),
                    )
                html_content = get_ticket_email_template(
                    ticket_payload,
                    event_payload,
                    pdf_url=None if attachment else document.public_url,
                    has_attachment=bool(attachment),
                )
                text_content = get_ticket_email_text(ticket_payload, event_payload)
                sent = self.mail_service.send(
                    EmailMessage(
                        to_email=participant.email,
                        subject=subject,
                        text_content=text_content,
                        html_content=html_content,
                        attachment=attachment,
                        category="ticket",
                    )
                )
                if not sent:
                    return {"success": False, "error": "Failed to send email"}
                participant.ticket_sent = True

            self.participant_repository.update_from_model(event_id, participant_id, participant)
            return {"success": True}

        except Exception as exc:
            self.logger.error("Error processing ticket: %s", redact_sensitive(str(exc)))
            self.log_failed_ticket_email(participant_id, participant_data, str(exc))
            return {"success": False, "error": str(exc)}

    def log_failed_ticket_email(self, participant_id: str, participant_data: Any, error_message: str) -> None:
        try:
            participant = self._normalize_participant(participant_data)
            message = ContactMessage(
                subject="Ticket email failed",
                participant_id=participant_id,
                event_id=participant.event_id,
                email=participant.email,
                name=participant.name,
                error_message=error_message,
                timestamp=firestore.SERVER_TIMESTAMP,
            )
            self.message_repository.create_from_model(message)
            self.logger.info("Ticket email failure logged for %s", participant_id)
        except Exception as exc:
            self.logger.error("Failed to log ticket email failure: %s", redact_sensitive(str(exc)))
