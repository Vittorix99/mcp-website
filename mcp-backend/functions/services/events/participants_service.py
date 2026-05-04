import logging
from datetime import datetime, timezone
from typing import Any, Optional, List

from google.cloud import firestore

from dto.participant_api import (
    CheckParticipantsResponseDTO,
    CheckoutParticipantRequestDTO,
    ParticipantActionResponseDTO,
    ParticipantCreateRequestDTO,
    ParticipantResponseDTO,
    ParticipantUpdateRequestDTO,
    SendOmaggioEmailsRequestDTO,
    SendOmaggioEmailsResponseDTO,
)
from domain.membership_rules import (
    build_renewal_record,
    membership_years_from_renewals,
)
from domain.participant_rules import run_basic_checks
from interfaces.repositories import (
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    ParticipantRepositoryProtocol,
)
from interfaces.services import MembershipsServiceProtocol, TicketServiceProtocol
from mappers.participant_mappers import (
    apply_participant_update_dto_to_model,
    create_participant_dto_to_model,
    participant_to_response,
)
from models import Event, EventParticipant, EventPurchaseAccessType, Membership, PaymentMethod
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from errors.service_errors import ConflictError, ExternalServiceError, NotFoundError, ValidationError, ForbiddenError
from services.events.ticket_service import TicketService
from services.memberships.renewal_command import RenewMembershipCommand
from services.communications.mail_service import EmailMessage, MailService, mail_service
from utils.templates_mail import get_omaggio_email_template, get_omaggio_email_text
from utils.events_utils import (
    calculate_end_of_year_membership,
    is_minor,
    normalize_email,
    normalize_phone,
)


class ParticipantsService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        ticket_service: Optional[TicketServiceProtocol] = None,
        memberships_service: Optional[MembershipsServiceProtocol] = None,
        mail_service_instance: Optional[MailService] = None,
    ):
        self.logger = logging.getLogger("ParticipantsService")
        self.event_repository = event_repository or EventRepository()
        self.membership_repository = membership_repository or MembershipRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.allowed_payment_methods = {method.value for method in PaymentMethod}
        self.ticket_service = ticket_service or TicketService()
        if memberships_service is None:
            from services.memberships.memberships_service import MembershipsService

            memberships_service = MembershipsService(
                membership_repository=self.membership_repository,
                participant_repository=self.participant_repository,
                event_repository=self.event_repository,
            )
        self.memberships_service = memberships_service
        self.mail_service = mail_service_instance or mail_service

    def _get_memberships_service(self) -> MembershipsServiceProtocol:
        memberships_service = getattr(self, "memberships_service", None)
        if memberships_service is None:
            from services.memberships.memberships_service import MembershipsService

            memberships_service = MembershipsService(
                membership_repository=self.membership_repository,
                participant_repository=self.participant_repository,
                event_repository=self.event_repository,
            )
            self.memberships_service = memberships_service
        return memberships_service

    def _normalize_price(self, price: Optional[Any]) -> Optional[float]:
        if price in (None, ""):
            return None
        try:
            return float(price)
        except (TypeError, ValueError):
            return None

    def _resolve_payment_method(
        self,
        payment_method: Optional[str],
        price_value: Optional[float],
        purchase_id: Optional[str],
    ) -> str:
        method = (payment_method or "").strip().lower()
        if purchase_id:
            return PaymentMethod.WEBSITE.value
        if price_value == 0:
            return PaymentMethod.OMAGGIO.value
        if not method:
            raise ValidationError("Missing payment_method")
        if method not in self.allowed_payment_methods:
            raise ValidationError("Invalid payment_method")
        return method

    def _find_membership(self, email: str, phone: str) -> Optional[Membership]:
        membership = self.membership_repository.find_by_email(email) if email else None
        if not membership and phone:
            membership = self.membership_repository.find_by_phone(phone)
        return membership

    def get_all(self, event_id: str) -> list[ParticipantResponseDTO]:
        participants = self.participant_repository.list(event_id)
        return [participant_to_response(participant) for participant in participants]

    def get_by_id(self, event_id: str, participant_id: str) -> ParticipantResponseDTO:
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")
        return participant_to_response(participant)

    def create(self, dto: ParticipantCreateRequestDTO) -> ParticipantActionResponseDTO:
        event_id = dto.event_id
        if not event_id:
            raise ValidationError("event_id is required")

        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        birthdate = dto.birthdate
        if not birthdate or is_minor(birthdate):
            raise ForbiddenError("Partecipante minorenne non consentito")

        email = dto.email or ""
        phone = dto.phone or ""
        membership_included = bool(dto.membership_included)
        purchase_id = dto.purchase_id
        price_value = self._normalize_price(dto.price)
        payment_method = self._resolve_payment_method(dto.payment_method, price_value, purchase_id)

        membership_id = None
        is_member = False
        membership = None
        explicit_membership_id = (
            dto.membership_id.strip()
            if isinstance(dto.membership_id, str)
            else dto.membership_id
        )

        if explicit_membership_id:
            membership = self.membership_repository.get(explicit_membership_id)
            if not membership:
                raise NotFoundError("Membership not found")
            membership_id = explicit_membership_id
            is_member = bool(membership.subscription_valid)
            membership_included = False
        else:
            membership = self._find_membership(email, phone)
            if membership:
                membership_id = membership.id
                is_member = bool(membership.subscription_valid)

        if membership_included and is_member:
            raise ConflictError("Questo utente è già un membro attivo")

        if membership_included and not is_member and membership_id:
            now = datetime.now(timezone.utc)
            start_date = now.isoformat()
            end_date = calculate_end_of_year_membership(now)
            # Il partecipante può includere una tessera: il rinnovo passa comunque dal service membership.
            membership = self._get_memberships_service().renew_existing(
                membership,
                RenewMembershipCommand(
                    membership_id=membership_id,
                    start_date=start_date,
                    end_date=end_date,
                    purchase_id=purchase_id or getattr(membership, "purchase_id", None),
                    fee=getattr(membership, "membership_fee", None),
                    membership_type="manual",
                    send_card=False,
                    invalidate_wallet=True,
                    create_wallet=False,
                    name=dto.name,
                    surname=dto.surname,
                    phone=phone,
                    birthdate=birthdate,
                ),
            )
            is_member = True

        if membership_included and not is_member and not membership_id:
            now = datetime.now(timezone.utc)
            start_date = now.isoformat()
            end_date = calculate_end_of_year_membership(now)
            renewals = [
                build_renewal_record(
                    start_date=start_date,
                    end_date=end_date,
                    purchase_id=None,
                    fee=None,
                )
            ]

            membership_model = Membership(
                name=dto.name or "",
                surname=dto.surname or "",
                email=email,
                phone=phone,
                birthdate=birthdate,
                start_date=start_date,
                end_date=end_date,
                subscription_valid=True,
                membership_sent=False,
                membership_type="manual",
                purchase_id=None,
                renewals=renewals,
                membership_years=membership_years_from_renewals(
                    renewals,
                    fallback_start_date=start_date,
                    fallback_end_date=end_date,
                ),
            )

            membership_id = self.membership_repository.create_from_model(membership_model)
            self.logger.info("Nuova membership creata: %s", membership_id)

        try:
            payment_enum = PaymentMethod(payment_method)
        except ValueError as exc:
            raise ValidationError("Invalid payment_method") from exc

        participant = create_participant_dto_to_model(
            dto,
            email=email,
            phone=phone,
            membership_id=membership_id,
            membership_included=bool(membership_id or membership_included),
            payment_method=payment_enum,
            price=price_value,
            created_at=firestore.SERVER_TIMESTAMP,
        )

        participant_id = self.participant_repository.create_from_model(event_id, participant)
        self.logger.info("Partecipante creato: %s", participant_id)

        if membership_id:
            self.membership_repository.add_attended_event(membership_id, event_id)

        return ParticipantActionResponseDTO(message="Participant created", id=participant_id)

    def update(
        self,
        event_id: str,
        participant_id: str,
        dto: ParticipantUpdateRequestDTO,
    ) -> ParticipantActionResponseDTO:
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")

        manual_membership_override = "membership_id" in dto.model_fields_set
        manual_membership_id = None
        if manual_membership_override:
            if dto.membership_id:
                membership = self.membership_repository.get(dto.membership_id)
                if not membership:
                    raise NotFoundError("Membership not found")
                manual_membership_id = dto.membership_id

        if participant.purchase_id and dto.payment_method is not None:
            raise ValidationError("Cannot change payment_method for website purchase")

        if participant.purchase_id and dto.price is not None:
            raise ValidationError("Modifica del prezzo non permessa: purchase già registrato")

        # Re-check membership when email changes
        should_update_membership = False
        new_membership_id = participant.membership_id  # default: keep existing
        clear_membership = False
        if not manual_membership_override and dto.email is not None:
            new_email = dto.email
            old_email = normalize_email(participant.email or "")
            if new_email != old_email:
                membership = self._find_membership(new_email, None)
                should_update_membership = True
                if membership:
                    new_membership_id = membership.id
                else:
                    new_membership_id = None
                    clear_membership = True

        updated_participant = apply_participant_update_dto_to_model(participant, dto)
        self.participant_repository.update_from_model(event_id, participant_id, updated_participant)

        if manual_membership_override:
            self.participant_repository.set_membership(event_id, participant_id, manual_membership_id)
        elif should_update_membership:
            if clear_membership:
                self.participant_repository.set_membership(event_id, participant_id, None)
            else:
                self.participant_repository.set_membership(event_id, participant_id, new_membership_id)

        return ParticipantActionResponseDTO(message="Participant updated", id=participant_id)

    def delete(self, event_id: str, participant_id: str) -> ParticipantActionResponseDTO:
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")
        self.participant_repository.delete(event_id, participant_id)
        return ParticipantActionResponseDTO(message="Participant deleted", id=participant_id)

    def send_ticket(self, event_id: str, participant_id: str) -> ParticipantActionResponseDTO:
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")

        result = self.ticket_service.process_new_ticket(participant_id, participant)
        if result.get("success"):
            return ParticipantActionResponseDTO(message="Ticket inviato con successo", id=participant_id)
        raise ExternalServiceError(result.get("error", "Errore durante l'invio"))

    def send_omaggio_emails(
        self,
        dto: SendOmaggioEmailsRequestDTO,
    ) -> SendOmaggioEmailsResponseDTO:
        event_id = dto.event_id
        entry_time = dto.entry_time
        participant_id = dto.participant_id
        skip_already_sent = dto.skip_already_sent

        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        all_participants = self.participant_repository.list(event_id)
        omaggi = [
            participant
            for participant in all_participants
            if (participant.payment_method.value if participant.payment_method else "").lower() == "omaggio"
        ]

        if participant_id:
            omaggi = [p for p in omaggi if p.id == participant_id]
            if not omaggi:
                raise NotFoundError("Omaggio non trovato")

        sent_count = 0
        failed_count = 0
        skipped_count = 0

        for p in omaggi:
            if skip_already_sent and bool(getattr(p, "omaggio_email_sent", False)):
                skipped_count += 1
                continue
            if not p.email:
                failed_count += 1
                continue
            sent = self._send_omaggio_email(event_model, p, entry_time)
            if sent:
                sent_count += 1
                p.omaggio_email_sent = True
                p.omaggio_email_sent_at = firestore.SERVER_TIMESTAMP
                self.participant_repository.update_from_model(event_id, p.id, p)
            else:
                failed_count += 1

        return SendOmaggioEmailsResponseDTO(
            sent=sent_count,
            failed=failed_count,
            skipped=skipped_count,
            total=len(omaggi),
            mode="single" if participant_id else "bulk",
        )

    def check_participants(
        self,
        event_id: str,
        participants: list[CheckoutParticipantRequestDTO],
    ) -> CheckParticipantsResponseDTO:
        if not event_id or not isinstance(participants, list) or not participants:
            raise ValidationError("eventId o participants mancanti")

        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        purchase_mode = event_model.purchase_mode or EventPurchaseAccessType.PUBLIC

        result = run_basic_checks(
            event_id,
            participants,
            event_model,
            participant_repository=self.participant_repository,
            membership_repository=self.membership_repository,
        )
        if result.errors:
            err = ValidationError("validation_error")
            err.details = result.errors
            raise err

        if purchase_mode == EventPurchaseAccessType.ON_REQUEST:
            return CheckParticipantsResponseDTO(valid=True, members=result.members, non_members=result.non_members)

        if purchase_mode == EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS and result.non_members:
            msg = (
                "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: "
                + ", ".join(result.non_members)
            )
            err = ValidationError("validation_error")
            err.details = [msg]
            raise err

        return CheckParticipantsResponseDTO(valid=True)

    def _send_omaggio_email(self, event_model: Event, participant: EventParticipant, entry_time: Optional[str]) -> bool:
        if not participant.email:
            return False

        name = f"{participant.name or ''} {participant.surname or ''}".strip() or "Ospite"
        html_content = get_omaggio_email_template(
            participant_name=name,
            event_title=event_model.title or "",
            event_date=event_model.date or "",
            event_location=event_model.location or "",
            entry_time=entry_time,
        )
        text_content = get_omaggio_email_text(
            participant_name=name,
            event_title=event_model.title or "",
            event_date=event_model.date or "",
            event_location=event_model.location or "",
            entry_time=entry_time,
        )
        subject = f"Il tuo invito – {event_model.title}"
        return self.mail_service.send(
            EmailMessage(
                to_email=participant.email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                attachment=None,
                category="omaggio",
            )
        )
