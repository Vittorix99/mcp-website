# services/admin/memberships_service.py

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from dto.membership_api import (
    CreateMembershipRequestDTO,
    MembershipActionResponseDTO,
    MembershipPriceResponseDTO,
    MembershipResponseDTO,
    MembershipWalletPassResponseDTO,
    RenewMembershipRequestDTO,
    UpdateMembershipRequestDTO,
    WalletModelResponseDTO,
)
from mappers.purchase_mappers import purchase_to_response
from mappers.membership_mappers import (
    apply_membership_update_dto_to_model,
    create_membership_dto_to_model,
    membership_to_response,
)
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
from services.memberships.renewal_command import RenewMembershipCommand
from services.events.documents_service import DocumentsService
from services.communications.mail_service import EmailMessage, MailService, mail_service
from errors.service_errors import (
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from utils.templates_mail import get_membership_email_template, get_membership_email_text
from utils.events_utils import (
    calculate_end_of_year_membership,
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

    def _membership_template_payload(self, membership: Membership, membership_id: str) -> Dict:
        payload = membership_to_response(membership).to_payload()
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
        # Il service compone la storia dei rinnovi; il repository si limita a persistere il model finale.
        renewals = list(existing.renewals or [])
        if not renewals:
            # Documenti legacy: prima del refactor renewal alcuni membri avevano
            # solo start_date/end_date e nessuna voce nello storico. Prima di
            # sovrascrivere start_date con il rinnovo nuovo, fissiamo il primo
            # anno di iscrizione nello storico per non far sparire il socio dal
            # filtro dell'anno originale.
            existing_year = parse_membership_year(existing.start_date, existing.end_date)
            if existing_year:
                renewals.append(
                    build_renewal_record(
                        start_date=existing.start_date,
                        end_date=existing.end_date,
                        purchase_id=existing.purchase_id,
                        fee=existing.membership_fee,
                        year=existing_year,
                    )
                )
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
        for value in existing.membership_years or []:
            try:
                years.append(int(value))
            except (TypeError, ValueError):
                continue
        return renewals, sorted(set(years))

    def renew_existing(
        self,
        existing: Membership,
        command: RenewMembershipCommand,
    ) -> Membership:
        """Entry point unico per rinnovare una membership già esistente."""
        membership_id = command.membership_id or existing.id
        if not membership_id:
            raise ValidationError("Membership id mancante")

        self.logger.info(f"[renew] Renewing membership {membership_id} (start_date: {existing.start_date})")

        # Il vecchio wallet non deve rappresentare una tessera rinnovata.
        if command.invalidate_wallet and existing.wallet_pass_id:
            try:
                self.pass2u_service.invalidate_membership_pass(existing.wallet_pass_id)
            except Exception as e:
                self.logger.warning(f"[renew] Old pass invalidation failed (non-blocking): {e}")

        renewals, membership_years = self._compose_renewals_and_years(
            existing,
            new_start_date=command.start_date,
            new_end_date=command.end_date,
            purchase_id=command.purchase_id,
            fee=command.fee if command.fee is not None else existing.membership_fee,
        )

        # Da qui in poi aggiorniamo solo il domain model; il repository persiste senza regole.
        existing.start_date = command.start_date
        existing.end_date = command.end_date
        existing.subscription_valid = True
        existing.membership_sent = False
        existing.send_card_on_create = command.send_card
        existing.renewals = renewals
        existing.membership_years = membership_years
        if command.invalidate_wallet or command.create_wallet:
            existing.wallet_pass_id = None
            existing.wallet_url = None
        if command.fee is not None:
            existing.membership_fee = command.fee
        if command.membership_type:
            existing.membership_type = command.membership_type
        if command.purchase_id:
            if not existing.purchase_id:
                existing.purchase_id = command.purchase_id
            existing.purchases = sorted({*(existing.purchases or []), command.purchase_id})
        if command.name and not existing.name:
            existing.name = command.name
        if command.surname and not existing.surname:
            existing.surname = command.surname
        if command.phone and not existing.phone:
            existing.phone = command.phone
        if command.birthdate and not existing.birthdate:
            existing.birthdate = command.birthdate

        self.membership_repository.update_from_model(membership_id, existing)

        if command.create_wallet:
            try:
                wallet = self.pass2u_service.create_membership_pass(membership_id, existing)
                if wallet:
                    existing.wallet_pass_id = wallet.pass_id
                    existing.wallet_url = wallet.wallet_url
                    self.membership_repository.update_from_model(membership_id, existing)
            except Exception as e:
                self.logger.warning(f"[renew] Pass creation failed (non-blocking): {e}")

        if command.send_card and existing.email:
            try:
                self.send_card(membership_id)
                existing.membership_sent = True
            except Exception as e:
                self.logger.warning(f"[renew] Card send failed (non-blocking): {e}")

        self.logger.info(f"[renew] Membership {membership_id} renewed successfully")
        return existing

    def _build_mergeable_conflict(self, conflicting: Membership) -> ConflictError:
        label = f"{(conflicting.name or '').strip()} {(conflicting.surname or '').strip()}".strip()
        err = ConflictError("Email già registrata per un altro membro")
        err.payload = {
            "mergeable": True,
            "conflicting_id": conflicting.id,
            "conflicting_name": label or conflicting.email or conflicting.id,
        }
        return err

    def get_all(self, year: int = None) -> list[MembershipResponseDTO]:
        if year:
            # membership_years è l'indice canonico degli anni associativi.
            memberships = self.membership_repository.find_by_year(int(year))
        else:
            memberships = self.membership_repository.list()
        return [membership_to_response(membership) for membership in memberships]

    def get_by_id(self, membership_id, slug: str = None) -> MembershipResponseDTO:
        membership = None
        if slug:
            membership = self.membership_repository.get_model_by_slug(slug)
        if membership is None and membership_id:
            membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership not found")
        return membership_to_response(membership)

    def create(self, dto: CreateMembershipRequestDTO) -> MembershipActionResponseDTO:
        birthdate = dto.birthdate
        minor_error = get_minor_validation_error(birthdate)
        if minor_error:
            raise ValidationError(minor_error)

        email = dto.email
        phone = dto.phone
        contact_error = get_missing_contact_validation_error(email, phone)
        if contact_error:
            raise ValidationError(contact_error)

        email_conflict = self.membership_repository.find_by_email(email) if email else None
        phone_conflict = self.membership_repository.find_by_phone(phone) if phone else None
        # Se il contatto appartiene a una membership scaduta, la create diventa un rinnovo.
        # Se invece la membership copre già l'anno corrente, è un vero conflitto.
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
        # Anche la prima iscrizione ha un renewal record: la cronologia parte dall'anno di creazione.
        renewal_record = build_renewal_record(
            start_date=start_date,
            end_date=end_date,
            purchase_id=None,
            fee=dto.membership_fee,
            year=start_year,
        )

        membership = create_membership_dto_to_model(
            dto,
            start_date=start_date,
            end_date=end_date,
            start_year=start_year,
        )
        membership.renewals = [renewal_record]

        membership_id = self.membership_repository.create_from_model(membership)
        self.logger.info(f"[create] Membership created with ID: {membership_id}")
        return MembershipActionResponseDTO(message="Membership created", id=membership_id)

    def _renew(
        self,
        membership_id: str,
        existing: Membership,
        dto: CreateMembershipRequestDTO | RenewMembershipRequestDTO,
    ) -> MembershipActionResponseDTO:
        """Rinnova una membership scaduta aggiornando il model e rigenerando la tessera."""
        now = datetime.now(timezone.utc)
        new_start = now.isoformat()
        new_end = calculate_end_of_year_membership(now)
        self.renew_existing(
            existing,
            RenewMembershipCommand(
                membership_id=membership_id,
                start_date=new_start,
                end_date=new_end,
                purchase_id=dto.purchase_id or None,
                fee=dto.membership_fee if dto.membership_fee is not None else existing.membership_fee,
                membership_type=dto.membership_type,
                send_card=bool(dto.send_card_on_create) if dto.send_card_on_create is not None else False,
                invalidate_wallet=True,
                create_wallet=True,
            ),
        )
        return MembershipActionResponseDTO(message="Membership rinnovata", id=membership_id, renewed=True)

    def renew(self, membership_id: str, dto: RenewMembershipRequestDTO) -> MembershipActionResponseDTO:
        """Public endpoint: manually renew a membership for the current year."""
        existing = self.membership_repository.get(membership_id)
        if not existing:
            raise NotFoundError("Membership non trovata")
        return self._renew(membership_id, existing, dto)

    def update(self, membership_id, dto: UpdateMembershipRequestDTO) -> MembershipActionResponseDTO:
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        birthdate = dto.birthdate if dto.birthdate is not None else membership.birthdate
        minor_error = get_minor_validation_error(birthdate)
        if minor_error:
            raise ValidationError(minor_error)

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

        updated_membership = apply_membership_update_dto_to_model(membership, dto)
        updated_membership.birthdate = birthdate

        # [WALLET MIGRATION] Rigenerazione PDF tessera su cambio email commentata
        #     dto.membership_sent = False

        self.membership_repository.update_from_model(membership_id, updated_membership)
        return MembershipActionResponseDTO(message="Membership aggiornata", id=membership_id)


    def create_wallet_pass(self, membership_id: str) -> MembershipWalletPassResponseDTO:
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        wallet = self.pass2u_service.create_membership_pass(membership_id, membership)
        if not wallet:
            raise ExternalServiceError("Impossibile creare il wallet pass (Pass2U ha restituito None)")

        membership.wallet_pass_id = wallet.pass_id
        membership.wallet_url = wallet.wallet_url
        self.membership_repository.update_from_model(membership_id, membership)
        return MembershipWalletPassResponseDTO(wallet_pass_id=wallet.pass_id, wallet_url=wallet.wallet_url)

    def invalidate_wallet_pass(self, membership_id: str) -> MembershipActionResponseDTO:
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        pass_id = membership.wallet_pass_id
        if not pass_id:
            return MembershipActionResponseDTO(message="Nessun wallet pass da invalidare", id=membership_id)

        ok = self.pass2u_service.invalidate_membership_pass(pass_id)
        if ok:
            membership.wallet_pass_id = None
            membership.wallet_url = None
            self.membership_repository.update_from_model(membership_id, membership)
        return MembershipActionResponseDTO(
            message="Wallet pass invalidato" if ok else "Invalidazione fallita (pass rimosso localmente)",
            id=membership_id,
        )

    def delete(self, membership_id) -> MembershipActionResponseDTO:
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership non trovata")

        # Invalida il wallet pass se presente
        if membership.wallet_pass_id:
            try:
                self.pass2u_service.invalidate_membership_pass(membership.wallet_pass_id)
                self.logger.info("[delete] Wallet pass %s invalidato", membership.wallet_pass_id)
            except Exception as e:
                self.logger.warning("[delete] Invalidazione wallet pass fallita (non bloccante): %s", e)

        storage_path = membership.card_storage_path
        if storage_path and self.storage is not None:
            blob = self.storage.blob(storage_path)
            if blob.exists():
                blob.delete()
                self.logger.info("[delete] Tessera rimossa dallo storage: %s", storage_path)

        removed = self.participant_repository.clear_membership_reference(membership_id)
        if removed:
            self.logger.info("[delete] Rimosso membershipId da %d partecipanti", removed)

        self.membership_repository.delete(membership_id)
        return MembershipActionResponseDTO(message="Membership eliminata e tessera rimossa", id=membership_id)

    def send_card(self, membership_id) -> MembershipActionResponseDTO:
        membership = self.membership_repository.get(membership_id)
        if not membership:
            raise NotFoundError("Membership not found")

        membership_payload = self._membership_template_payload(membership, membership_id)
        email = membership.email


        # Recupera o genera wallet_url on-demand
        wallet_url = membership.wallet_url
        if not wallet_url:
            try:
                wallet = self.pass2u_service.create_membership_pass(membership_id, membership)
                if wallet:
                    membership.wallet_pass_id = wallet.pass_id
                    membership.wallet_url = wallet.wallet_url
                    wallet_url = wallet.wallet_url
                    self.membership_repository.update_from_model(membership_id, membership)
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

        membership.membership_sent = True
        self.membership_repository.update_from_model(membership_id, membership)
        return MembershipActionResponseDTO(message="Card sent successfully", id=membership_id)
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
                purchases.append(purchase_to_response(purchase_model).to_payload())

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
                events.append({"id": event.id, "title": event.title, "date": event.date, "image": event.image}) # To modify approach 

        return events
    def set_membership_price(self, price, year=None) -> MembershipPriceResponseDTO:
        year = str(year or datetime.now().year)
        numeric_price = float(price)
        self.settings_repository.set_price_by_year(year, numeric_price)
        return MembershipPriceResponseDTO(
            year=year,
            price=numeric_price,
            message=f"Prezzo membership per {year} aggiornato a {numeric_price}",
        )
    
    def get_membership_price(self, year=None) -> MembershipPriceResponseDTO:
        year = str(year or datetime.now().year)
        price = self.settings_repository.get_price_by_year(year)
        if price is None:
            raise NotFoundError(f"Nessun prezzo configurato per l'anno {year}")
        return MembershipPriceResponseDTO(year=year, price=float(price))

    def get_wallet_model(self) -> WalletModelResponseDTO:
        model_id = self.settings_repository.get_wallet_model()
        if not model_id:
            raise NotFoundError("Wallet model non configurato")
        return WalletModelResponseDTO(model_id=model_id)

    def set_wallet_model(self, model_id: str) -> WalletModelResponseDTO:
        self.settings_repository.set_wallet_model(model_id)
        return WalletModelResponseDTO(
            model_id=model_id,
            message="Wallet model aggiornato",
        )
