# services/admin/memberships_service.py

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from dto import EventDTO, MembershipDTO, PurchaseDTO
from models import Membership
from domain.membership_rules import (
    build_renewal_record,
    get_minor_validation_error,
    get_missing_contact_validation_error,
    is_membership_renewable,
    membership_years_from_renewals,
    parse_membership_year,
    resolve_membership_contact_conflict,
)
from interfaces.repositories import (
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    MembershipSettingsRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from interfaces.services import DocumentsServiceProtocol, Pass2UServiceProtocol
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.memberships.pass2u_service import Pass2UService
from services.events.documents_service import DocumentsService
from services.communications.mail_service import EmailMessage, MailService, mail_service
from errors.service_errors import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from utils.templates_mail import get_membership_email_template, get_membership_email_text
from utils.events_utils import (
    calculate_end_of_year_membership,
    normalize_email,
    normalize_phone,
    validate_email_format,
)


class MembershipsService:
    def __init__(
        self,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        settings_repository: Optional[MembershipSettingsRepositoryProtocol] = None,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        event_repository: Optional[EventRepositoryProtocol] = None,
        documents_service: Optional[DocumentsServiceProtocol] = None,
        pass2u_service: Optional[Pass2UServiceProtocol] = None,
        mail_service_instance: Optional[MailService] = None,
    ):
        self.logger = logging.getLogger("MembershipsService")
        self.membership_repository = membership_repository or MembershipRepository()
        self.settings_repository = settings_repository or MembershipSettingsRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.event_repository = event_repository or EventRepository()
        self.documents_service = documents_service or DocumentsService()
        self.pass2u_service = pass2u_service or Pass2UService()
        self.mail_service = mail_service_instance or mail_service

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

    def _compose_renewals_and_years(
        self,
        existing: Membership,
        *,
        new_start_date: str,
        new_end_date: str,
        purchase_id: Optional[str],
        fee: Optional[float],
    ) -> tuple[list[dict], list[int]]:
        renewals = list(existing.renewals or [])
        renewals.append(
            build_renewal_record(
                start_date=new_start_date,
                end_date=new_end_date,
                purchase_id=purchase_id,
                fee=fee,
            )
        )
        years = membership_years_from_renewals(
            renewals,
            fallback_start_date=new_start_date,
            fallback_end_date=new_end_date,
        )
        return renewals, years

    def _build_mergeable_conflict(self, conflicting: Membership) -> ConflictError:
        label = f"{(conflicting.name or '').strip()} {(conflicting.surname or '').strip()}".strip()
        err = ConflictError("Email già registrata per un altro membro")
        err.payload = {
            "mergeable": True,
            "conflicting_id": conflicting.id,
            "conflicting_name": label or conflicting.email or conflicting.id,
        }
        return err

    def get_all(self, year: int = None):
        if year:
            memberships = self.membership_repository.find_by_year(year)
        else:
            memberships = self.membership_repository.list()
        return [MembershipDTO.from_model(m).to_payload() for m in memberships]

    def get_by_id(self, membership_id, slug: str = None):
        membership = None
        if slug:
            membership = self.membership_repository.get_model_by_slug(slug)
        if membership is None and membership_id:
            membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership not found")
        return self._membership_payload(membership)

    def create(self, dto: MembershipDTO):
        protected_error = dto.validate_protected_fields()
        if protected_error:
            raise ForbiddenError(protected_error)

        birthdate = dto.birthdate
        minor_error = get_minor_validation_error(birthdate)
        if minor_error:
            raise ValidationError(minor_error)

        email = normalize_email(dto.email) or None
        phone = normalize_phone(dto.phone) or None
        if email and not validate_email_format(email):
            raise ValidationError("Formato email non valido")
        contact_error = get_missing_contact_validation_error(email, phone)
        if contact_error:
            raise ValidationError(contact_error)

        email_conflict = self.membership_repository.find_by_email(email) if email else None
        phone_conflict = self.membership_repository.find_by_phone(phone) if phone else None
        if email:
            if email_conflict:
                if is_membership_renewable(email_conflict):
                    return self._renew(email_conflict.id, email_conflict, dto)
                raise ConflictError("Email già registrata")
        if phone:
            if phone_conflict:
                if is_membership_renewable(phone_conflict):
                    return self._renew(phone_conflict.id, phone_conflict, dto)
                raise ConflictError("Telefono già registrato")

        now = datetime.now(timezone.utc)
        start_date = now.isoformat()
        end_date = calculate_end_of_year_membership(now)
        start_year = parse_membership_year(start_date, end_date)
        renewal_record = build_renewal_record(
            start_date=start_date,
            end_date=end_date,
            purchase_id=None,
            fee=dto.membership_fee,
            year=start_year,
        )

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
            renewals=[renewal_record],
            membership_years=[start_year] if start_year else [],
        )

        membership_id = self.membership_repository.create_from_model(membership)
        self.logger.info(f"[create] Membership created with ID: {membership_id}")
        return {'message': 'Membership created', 'id': membership_id}

    def _renew(self, membership_id: str, existing: Membership, dto: MembershipDTO) -> Dict:
        """Renews an expired membership: updates dates, invalidates old pass, creates new one."""
        self.logger.info(f"[renew] Renewing membership {membership_id} (start_date: {existing.start_date})")

        # 1. Invalidate old pass
        if existing.wallet_pass_id:
            try:
                self.pass2u_service.invalidate_membership_pass(existing.wallet_pass_id)
            except Exception as e:
                self.logger.warning(f"[renew] Old pass invalidation failed (non-blocking): {e}")

        # 2. Update membership with new dates and clear old wallet data
        now = datetime.now(timezone.utc)
        new_start = now.isoformat()
        new_end = calculate_end_of_year_membership(now)
        renewals, membership_years = self._compose_renewals_and_years(
            existing,
            new_start_date=new_start,
            new_end_date=new_end,
            purchase_id=None,
            fee=dto.membership_fee if dto.membership_fee is not None else existing.membership_fee,
        )

        updates = {
            "start_date": new_start,
            "end_date": new_end,
            "subscription_valid": True,
            "membership_sent": False,
            "renewals": renewals,
            "membership_years": membership_years,
        }
        if dto.membership_fee is not None:
            updates["membership_fee"] = dto.membership_fee
        if dto.membership_type:
            updates["membership_type"] = dto.membership_type
        self.membership_repository.update_fields(membership_id, updates)
        self.membership_repository.clear_wallet(membership_id)

        # 3. Create new pass
        updated = self.membership_repository.get(membership_id)
        try:
            wallet = self.pass2u_service.create_membership_pass(membership_id, updated)
            if wallet:
                self.membership_repository.set_wallet(membership_id, wallet.pass_id, wallet.wallet_url)
        except Exception as e:
            self.logger.warning(f"[renew] Pass creation failed (non-blocking): {e}")

        # 4. Send card if requested
        send_card = bool(dto.send_card_on_create) if dto.send_card_on_create is not None else False
        if send_card and existing.email:
            try:
                self.send_card(membership_id)
            except Exception as e:
                self.logger.warning(f"[renew] Card send failed (non-blocking): {e}")

        self.logger.info(f"[renew] Membership {membership_id} renewed successfully")
        return {"message": "Membership rinnovata", "id": membership_id, "renewed": True}

    def update(self, membership_id, dto: MembershipDTO):
        protected_error = dto.validate_protected_fields()
        if protected_error:
            raise ForbiddenError(protected_error)

        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        birthdate = dto.birthdate if dto.birthdate is not None else membership.birthdate
        minor_error = get_minor_validation_error(birthdate)
        if minor_error:
            raise ValidationError(minor_error)

        if dto.email is not None:
            dto.email = normalize_email(dto.email) or None
            if dto.email and not validate_email_format(dto.email):
                raise ValidationError("Formato email non valido")
        if dto.phone is not None:
            dto.phone = normalize_phone(dto.phone) or None

        effective_email = dto.email if dto.email is not None else membership.email
        effective_phone = dto.phone if dto.phone is not None else membership.phone

        contact_error = get_missing_contact_validation_error(effective_email, effective_phone)
        if contact_error:
            raise ValidationError(contact_error)

        email_conflict = None
        phone_conflict = None
        if dto.email is not None and effective_email:
            email_conflict = self.membership_repository.find_by_email(effective_email)
        if dto.phone is not None and effective_phone:
            phone_conflict = self.membership_repository.find_by_phone(effective_phone)

        conflict = resolve_membership_contact_conflict(
            current_membership_id=membership_id,
            email_membership=email_conflict,
            phone_membership=phone_conflict,
        )
        if conflict:
            field_name, conflicting_membership = conflict
            if field_name == "email":
                raise self._build_mergeable_conflict(conflicting_membership)
            raise ConflictError("Telefono già registrato per un altro membro")

        dto.apply_updates(membership)
        if dto.birthdate is not None:
            membership.birthdate = birthdate

        # [WALLET MIGRATION] Rigenerazione PDF tessera su cambio email commentata
        # if dto.email is not None and membership.email and membership.email != previous_email:
        #     try:
        #         document = self.documents_service.create_membership_card(
        #             membership_id,
        #             MembershipDTO.from_model(membership),
        #         )
        #     except Exception as exc:
        #         raise ExternalServiceError(
        #             f"Errore durante la rigenerazione della tessera: {exc}"
        #         ) from exc
        #     membership.card_url = document.public_url
        #     membership.card_storage_path = document.storage_path
        #     membership.membership_sent = False
        #     dto.card_url = membership.card_url
        #     dto.card_storage_path = membership.card_storage_path
        #     dto.membership_sent = False

        self.membership_repository.update_from_model(membership_id, dto)
        return {'message': 'Membership aggiornata'}


    def create_wallet_pass(self, membership_id: str):
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        wallet = self.pass2u_service.create_membership_pass(membership_id, membership)
        if not wallet:
            raise ExternalServiceError("Impossibile creare il wallet pass (Pass2U ha restituito None)")

        self.membership_repository.update_from_model(
            membership_id,
            MembershipDTO(wallet_pass_id=wallet.pass_id, wallet_url=wallet.wallet_url),
        )
        return {"wallet_pass_id": wallet.pass_id, "wallet_url": wallet.wallet_url}

    def invalidate_wallet_pass(self, membership_id: str):
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        pass_id = membership.wallet_pass_id
        if not pass_id:
            return {"message": "Nessun wallet pass da invalidare"}

        ok = self.pass2u_service.invalidate_membership_pass(pass_id)
        if ok:
            self.membership_repository.clear_wallet(membership_id)
        return {"message": "Wallet pass invalidato" if ok else "Invalidazione fallita (pass rimosso localmente)"}

    def delete(self, membership_id):
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        # Invalida il wallet pass se presente
        if membership.wallet_pass_id:
            try:
                self.pass2u_service.invalidate_membership_pass(membership.wallet_pass_id)
                print(f"[Pass2U] Wallet pass {membership.wallet_pass_id} invalidato")
            except Exception as e:
                print(f"[Pass2U] Invalidazione wallet pass fallita (non bloccante): {e}")

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
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership not found")

        membership_payload = self._membership_template_payload(membership, membership_id)
        email = membership.email

        # [WALLET MIGRATION] Generazione/recupero PDF tessera commentata
        # card_url = membership.card_url
        # storage_path = membership.card_storage_path
        # document_buffer = None
        # if not card_url:
        #     try:
        #         document = self.documents_service.create_membership_card(
        #             membership_id,
        #             MembershipDTO.from_model(membership),
        #         )
        #     except Exception as exc:
        #         raise ExternalServiceError(f"Card generation failed: {exc}") from exc
        #     card_url = document.public_url
        #     storage_path = document.storage_path
        #     document_buffer = document.buffer
        #     self.membership_repository.update_from_model(
        #         membership_id,
        #         MembershipDTO(card_url=card_url, card_storage_path=storage_path, membership_sent=False),
        #     )
        #
        # if "memberships/cards/" not in card_url:
        #     raise ValidationError("Invalid card_url format")
        #
        # if not storage_path:
        #     path_start = card_url.find("memberships/cards/")
        #     storage_path = card_url[path_start:]
        #
        # if document_buffer is None:
        #     blob = self.storage.blob(storage_path)
        #     pdf_data = blob.download_as_bytes()
        #     document_buffer = BytesIO(pdf_data)

        # Recupera o genera wallet_url on-demand
        wallet_url = membership.wallet_url
        if not wallet_url:
            try:
                wallet = self.pass2u_service.create_membership_pass(membership_id, membership)
                if wallet:
                    wallet_url = wallet.wallet_url
                    self.membership_repository.update_from_model(
                        membership_id,
                        MembershipDTO(wallet_pass_id=wallet.pass_id, wallet_url=wallet_url),
                    )
            except Exception as exc:
                self.logger.warning(f"[Pass2U] wallet generation failed for {membership_id}: {exc}")

        membership_payload["wallet_url"] = wallet_url

        subject = "La tua tessera MCP"
        html_content = get_membership_email_template(membership_payload)
        text_content = get_membership_email_text(membership_payload)

        # [WALLET MIGRATION] EmailAttachment PDF commentato — email inviata senza allegato
        # attachment = EmailAttachment(
        #     content=document_buffer.getvalue(),
        #     filename=f"{name}_{surname}_membership.pdf",
        # )
        sent = self.mail_service.send(
            EmailMessage(
                to_email=email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                attachment=None,
                category="membership",
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
        membership = self.membership_repository.get(membership_id)
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
        membership = self.membership_repository.get(membership_id)
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
