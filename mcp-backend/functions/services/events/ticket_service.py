import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, Optional

from google.cloud import firestore

from config.firebase_config import db
from dto import EventDTO, EventParticipantDTO
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from services.events.documents_service import DocumentsService
from services.communications.mail_service import EmailAttachment, EmailMessage, mail_service
from utils.templates_mail import get_ticket_email_template, get_ticket_email_text


@dataclass
class TicketDocument:
    storage_path: str
    public_url: str
    buffer: Optional[BytesIO] = None

    def to_update_payload(self, sent: bool = False) -> Dict[str, Any]:
        return {"ticket_pdf_url": self.public_url, "ticket_sent": sent}


class TicketService:
    def __init__(
        self,
        documents_service: Optional[DocumentsService] = None,
        event_repository: Optional[EventRepository] = None,
        participant_repository: Optional[ParticipantRepository] = None,
    ):
        self.logger = logging.getLogger("TicketService")
        self.documents_service = documents_service or DocumentsService()
        self.event_repository = event_repository or EventRepository()
        self.participant_repository = participant_repository or ParticipantRepository()

    def _normalize_participant(self, payload: Any) -> EventParticipantDTO:
        if isinstance(payload, EventParticipantDTO):
            return payload
        if hasattr(payload, "to_payload"):
            return EventParticipantDTO.from_payload(payload.to_payload())
        if isinstance(payload, dict):
            return EventParticipantDTO.from_payload(payload)
        raise ValueError("participant_data must be a dict or EventParticipantDTO")

    def _normalize_event_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, EventDTO):
            return payload.to_payload()
        if hasattr(payload, "to_payload"):
            return payload.to_payload()
        if isinstance(payload, dict):
            return dict(payload)
        raise ValueError("event_data must be a dict or EventDTO")

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
        participant_payload = self._normalize_participant(participant_data).to_payload()
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
            participant_dto = self._normalize_participant(participant_data)
            event_id = participant_dto.event_id
            if not event_id:
                self.logger.warning("Missing event_id")
                return {"success": False, "error": "Missing event_id"}

            event_model = self.event_repository.get_model(event_id)
            if not event_model:
                return {"success": False, "error": f"Event {event_id} not found"}
            event_payload = EventDTO.from_model(event_model).to_payload()

            document = self.create_ticket_document(participant_dto, event_payload)
            update_payload = document.to_update_payload(sent=False)

            if send:
                if not participant_dto.email:
                    return {"success": False, "error": "Missing participant email"}
                ticket_payload = participant_dto.to_payload()
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
                sent = mail_service.send(
                    EmailMessage(
                        to_email=participant_dto.email,
                        subject=subject,
                        text_content=text_content,
                        html_content=html_content,
                        attachment=attachment,
                        category="ticket",
                    )
                )
                if not sent:
                    return {"success": False, "error": "Failed to send email"}
                update_payload["ticket_sent"] = True

            self.participant_repository.update(event_id, participant_id, update_payload)
            return {"success": True}

        except Exception as exc:
            self.logger.exception("Error processing ticket")
            self.log_failed_ticket_email(participant_id, participant_data, str(exc))
            return {"success": False, "error": str(exc)}

    def log_failed_ticket_email(self, participant_id: str, participant_data: Any, error_message: str) -> None:
        try:
            participant_dto = self._normalize_participant(participant_data)
            db.collection("contact_message").add(
                {
                    "subject": "Ticket email failed",
                    "participant_id": participant_id,
                    "event_id": participant_dto.event_id,
                    "email": participant_dto.email,
                    "name": participant_dto.name,
                    "surname": participant_dto.surname,
                    "error_message": error_message,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                }
            )
            self.logger.info("Ticket email failure logged for %s", participant_id)
        except Exception:
            self.logger.exception("Failed to log ticket email failure")
