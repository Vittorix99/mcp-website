# services/admin/memberships_service.py

import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict

from dto import EventDTO, MembershipDTO, PurchaseDTO
from models import Membership
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.documents_service import DocumentsService
from services.mail_service import EmailAttachment, EmailMessage, mail_service
from services.service_errors import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from utils.templates_mail import get_membership_email_template, get_membership_email_text
from utils.events_utils import calculate_end_of_year_membership, is_minor, normalize_email, normalize_phone


class MembershipsService:
    def __init__(self):
        self.logger = logging.getLogger("MembershipsService")
        self.membership_repository = MembershipRepository()
        self.settings_repository = MembershipSettingsRepository()
        self.purchase_repository = PurchaseRepository()
        self.participant_repository = ParticipantRepository()
        self.event_repository = EventRepository()
        self.documents_service = DocumentsService()

    @property
    def storage(self):
        return self.documents_service.storage

    def _membership_payload(self, membership: Membership) -> Dict:
        dto = MembershipDTO.from_model(membership)
        return dto.to_payload()

    def _membership_template_payload(self, membership: Membership, membership_id: str) -> Dict:
        payload = MembershipDTO.from_model(membership).to_payload()
        payload["membership_id"] = membership_id
        return payload

    def get_all(self):
        memberships = self.membership_repository.get_all()
        return [membership.to_payload() for membership in memberships]

    def get_by_id(self, membership_id, slug: str = None):
        membership = None
        if slug:
            membership = self.membership_repository.get_model_by_slug(slug)
        if membership is None and membership_id:
            membership = self.membership_repository.get_model(membership_id)
        if not membership:
            raise NotFoundError("Membership not found")
        return self._membership_payload(membership)

    def create(self, dto: MembershipDTO):
        protected_error = dto.validate_protected_fields()
        if protected_error:
            raise ForbiddenError(protected_error)

        birthdate = dto.birthdate
        if not birthdate or is_minor(birthdate):
            raise ValidationError("Utente minorenne non ammesso")

        email = normalize_email(dto.email) or None
        phone = normalize_phone(dto.phone) or None
        if not email and not phone:
            raise ValidationError("Email o telefono obbligatorio")

        if email:
            existing = self.membership_repository.find_by_email(email)
            if existing:
                raise ConflictError("Email già registrata")
        if phone:
            existing = self.membership_repository.find_by_phone(phone)
            if existing:
                raise ConflictError("Telefono già registrato")

        now = datetime.now(timezone.utc)
        start_date = now.isoformat()
        end_date = calculate_end_of_year_membership(now)

        send_card_on_create = bool(dto.send_card_on_create) if dto.send_card_on_create is not None else False

        membership = Membership(
            name=dto.name or "",
            surname=dto.surname or "",
            email=email,
            phone=phone,
            birthdate=birthdate,
            start_date=start_date,
            end_date=end_date,
            subscription_valid=True,
            membership_sent=False,
            membership_type=dto.membership_type or "manual",
            purchase_id=None,
            send_card_on_create=send_card_on_create,
            membership_fee=dto.membership_fee,
        )

        membership_id = self.membership_repository.create_from_model(membership)
        self.logger.info(f"[create] Membership created with ID: {membership_id}")
        return {'message': 'Membership created', 'id': membership_id}

    def update(self, membership_id, dto: MembershipDTO):
        protected_error = dto.validate_protected_fields()
        if protected_error:
            raise ForbiddenError(protected_error)

        membership = self.membership_repository.get_model(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        previous_email = membership.email
        birthdate = dto.birthdate if dto.birthdate is not None else membership.birthdate
        if not birthdate or is_minor(birthdate):
            raise ValidationError("Utente minorenne non ammesso")

        if dto.email is not None:
            dto.email = normalize_email(dto.email) or None
        if dto.phone is not None:
            dto.phone = normalize_phone(dto.phone) or None

        effective_email = dto.email if dto.email is not None else membership.email
        effective_phone = dto.phone if dto.phone is not None else membership.phone

        if not effective_email and not effective_phone:
            raise ValidationError("Email o telefono obbligatorio")

        if dto.email is not None and effective_email:
            existing = self.membership_repository.find_by_email(effective_email)
            if existing and existing[0] != membership_id:
                raise ConflictError("Email già registrata per un altro membro")
        if dto.phone is not None and effective_phone:
            existing = self.membership_repository.find_by_phone(effective_phone)
            if existing and existing[0] != membership_id:
                raise ConflictError("Telefono già registrato per un altro membro")

        dto.apply_updates(membership)
        if dto.birthdate is not None:
            membership.birthdate = birthdate

        if dto.email is not None and membership.email and membership.email != previous_email:
            try:
                document = self.documents_service.create_membership_card(
                    membership_id,
                    MembershipDTO.from_model(membership),
                )
            except Exception as exc:
                raise ExternalServiceError(
                    f"Errore durante la rigenerazione della tessera: {exc}"
                ) from exc
            membership.card_url = document.public_url
            membership.card_storage_path = document.storage_path
            membership.membership_sent = False
            dto.card_url = membership.card_url
            dto.card_storage_path = membership.card_storage_path
            dto.membership_sent = False

        self.membership_repository.update_from_model(membership_id, dto)
        return {'message': 'Membership aggiornata'}


    def delete(self, membership_id):
        membership = self.membership_repository.get_model(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        storage_path = membership.card_storage_path
        if storage_path and self.storage is not None:
            blob = self.storage.blob(storage_path)
            if blob.exists():
                blob.delete()
                print(f"Tessera rimossa dallo storage: {storage_path}")

        removed = self.participant_repository.clear_membership_reference(membership_id)
        if removed:
            print(f"Rimosso membershipId da {removed} partecipanti")

        self.membership_repository.delete(membership_id)
        return {'message': 'Membership eliminata e tessera rimossa'}

    def send_card(self, membership_id):
        membership = self.membership_repository.get_model(membership_id)
        if not membership:
            raise NotFoundError("Membership not found")

        membership_dto = MembershipDTO.from_model(membership)
        membership_payload = self._membership_template_payload(membership, membership_id)
        email = membership.email
        name = membership.name
        surname = membership.surname
        full_name = f"{name}_{surname}"

        card_url = membership.card_url
        storage_path = membership.card_storage_path
        document_buffer = None
        if not card_url:
            try:
                document = self.documents_service.create_membership_card(
                    membership_id,
                    membership_dto,
                )
            except Exception as exc:
                raise ExternalServiceError(f"Card generation failed: {exc}") from exc
            card_url = document.public_url
            storage_path = document.storage_path
            document_buffer = document.buffer
            self.membership_repository.update_from_model(
                membership_id,
                MembershipDTO(card_url=card_url, card_storage_path=storage_path, membership_sent=False),
            )

        if "memberships/cards/" not in card_url:
            raise ValidationError("Invalid card_url format")

        if not storage_path:
            path_start = card_url.find("memberships/cards/")
            storage_path = card_url[path_start:]

        if document_buffer is None:
            blob = self.storage.blob(storage_path)
            pdf_data = blob.download_as_bytes()
            document_buffer = BytesIO(pdf_data)

        subject = "La tua tessera MCP"
        html_content = get_membership_email_template(membership_payload)
        text_content = get_membership_email_text(membership_payload)

        attachment = None
        if document_buffer:
            attachment = EmailAttachment(
                content=document_buffer.getvalue(),
                filename=f"{full_name}_membership.pdf",
            )
        sent = mail_service.send(
            EmailMessage(
                to_email=email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                attachment=attachment,
            )
        )

        if not sent:
            raise ExternalServiceError("Failed to send email")

        self.membership_repository.update_from_model(
            membership_id,
            MembershipDTO(membership_sent=True),
        )
        return {'message': 'Card sent successfully'}
    def get_purchases(self, membership_id):
        membership = self.membership_repository.get_model(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        purchase_ids = membership.purchases or []
        if not purchase_ids:
            return []

        purchases = []
        for pid in purchase_ids:
            purchase_model = self.purchase_repository.get_model(pid)
            if purchase_model:
                payload = PurchaseDTO.from_model(purchase_model).to_payload()
                payload["id"] = purchase_model.id
                purchases.append(payload)

        return purchases
    def get_events(self, membership_id):
        membership = self.membership_repository.get_model(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        event_ids = membership.attended_events or []
        if not event_ids:
            return []

        events = []
        for eid in event_ids:
            event = self.event_repository.get_model(eid)
            if event:
                events.append(EventDTO.from_model(event).membership_event_payload())

        return events
    def set_membership_price(self, price, year=None):
        year = str(year or datetime.now().year)
        self.settings_repository.set_price_by_year(year, price)
        return {"message": f"Prezzo membership per {year} aggiornato a {price}"}
    
    def get_membership_price(self, year=None):
        year = str(year or datetime.now().year)
        price = self.settings_repository.get_price_by_year(year)
        if price is None:
            raise NotFoundError(f"Nessun prezzo configurato per l'anno {year}")
        return {"year": year, "price": price}
