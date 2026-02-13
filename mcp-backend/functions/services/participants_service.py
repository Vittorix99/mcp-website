import logging
from datetime import datetime, timezone
from typing import Any, Optional, List

from google.cloud import firestore

from dto import EventDTO, EventParticipantDTO, MembershipDTO
from dto.preorder import CheckoutParticipantDTO
from models import EventParticipant, EventPurchaseAccessType, Membership, PaymentMethod
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from services.service_errors import ConflictError, ExternalServiceError, NotFoundError, ValidationError, ForbiddenError
from services.ticket_service import TicketService
from utils.events_utils import (
    calculate_end_of_year_membership,
    is_minor,
    normalize_email,
    normalize_phone,
)
from domain.participant_rules import run_basic_checks


class ParticipantsService:
    def __init__(self):
        self.logger = logging.getLogger("ParticipantsService")
        self.event_repository = EventRepository()
        self.membership_repository = MembershipRepository()
        self.participant_repository = ParticipantRepository()
        self.allowed_payment_methods = {method.value for method in PaymentMethod}
        self.ticket_service = TicketService()

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
        membership = self.membership_repository.find_model_by_email(email) if email else None
        if not membership and phone:
            membership = self.membership_repository.find_model_by_phone(phone)
        return membership

    def get_all(self, event_id):
        participants = self.participant_repository.list(event_id)
        return [participant.to_payload() for participant in participants]

    def get_by_id(self, event_id, participant_id):
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")
        return participant.to_payload()

    def create(self, participant_data):
        dto = participant_data if isinstance(participant_data, EventParticipantDTO) else EventParticipantDTO.from_payload(participant_data)
        event_id = dto.event_id
        if not event_id:
            raise ValidationError("event_id is required")

        birthdate = dto.birthdate
        if not birthdate or is_minor(birthdate):
            raise ForbiddenError("Partecipante minorenne non consentito")

        email = normalize_email(dto.email)
        phone = normalize_phone(dto.phone)
        membership_included = bool(dto.membership_included)
        purchase_id = dto.purchase_id
        price_value = self._normalize_price(dto.price)
        payment_method = self._resolve_payment_method(dto.payment_method, price_value, purchase_id)

        membership_id = None
        is_member = False
        membership = self._find_membership(email, phone)
        if membership:
            membership_id = membership.id
            is_member = bool(membership.subscription_valid)

        if membership_included and is_member:
            raise ConflictError("Questo utente è già un membro attivo")

        if membership_included and not is_member and membership_id:
            now = datetime.now(timezone.utc)
            end_date = calculate_end_of_year_membership(now)
            update_dto = MembershipDTO(
                subscription_valid=True,
                start_date=now.isoformat(),
                end_date=end_date,
                membership_sent=False,
                membership_type="manual",
            )
            self.membership_repository.update_from_model(membership_id, update_dto)
            is_member = True

        if membership_included and not is_member and not membership_id:
            now = datetime.now(timezone.utc)
            end_date = calculate_end_of_year_membership(now)

            membership_model = Membership(
                name=dto.name or "",
                surname=dto.surname or "",
                email=email,
                phone=phone,
                birthdate=birthdate,
                start_date=now.isoformat(),
                end_date=end_date,
                subscription_valid=True,
                membership_sent=False,
                membership_type="manual",
                purchase_id=None,
            )

            membership_id = self.membership_repository.create_from_model(membership_model)
            self.logger.info("Nuova membership creata: %s", membership_id)

        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        purchase_mode = event_model.purchase_mode or EventPurchaseAccessType.PUBLIC
        if purchase_mode == EventPurchaseAccessType.ONLY_MEMBERS and not (membership_id or is_member):
            raise ForbiddenError("Per eventi riservati ai membri è richiesta la membership attiva")

        try:
            payment_enum = PaymentMethod(payment_method)
        except ValueError as exc:
            raise ValidationError("Invalid payment_method") from exc

        participant = EventParticipant(
            event_id=event_id,
            name=dto.name or "",
            surname=dto.surname or "",
            email=email,
            phone=phone,
            birthdate=birthdate,
            membership_included=bool(membership_id or membership_included),
            membership_id=membership_id,
            payment_method=payment_enum,
            ticket_sent=bool(dto.ticket_sent) if dto.ticket_sent is not None else False,
            location_sent=bool(dto.location_sent) if dto.location_sent is not None else False,
            newsletter_consent=bool(dto.newsletter_consent) if dto.newsletter_consent is not None else False,
            price=price_value,
            purchase_id=purchase_id,
            created_at=firestore.SERVER_TIMESTAMP,
        )

        participant_id = self.participant_repository.create_from_model(event_id, participant)
        self.logger.info("Partecipante creato: %s", participant_id)

        if membership_id:
            self.membership_repository.add_attended_event(membership_id, event_id)

        return {"message": "Participant created", "id": participant_id}

    def update(self, event_id, participant_id, data):
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")

        update_dto = data if isinstance(data, EventParticipantDTO) else EventParticipantDTO.from_payload(data)

        if participant.purchase_id and update_dto.payment_method is not None:
            raise ValidationError("Cannot change payment_method for website purchase")

        if participant.purchase_id and update_dto.price is not None:
            raise ValidationError("Modifica del prezzo non permessa: purchase già registrato")

        self.participant_repository.update(event_id, participant_id, update_dto)
        return {"message": "Participant updated"}

    def delete(self, event_id, participant_id):
        self.participant_repository.delete(event_id, participant_id)
        return {"message": "Participant deleted"}

    def send_ticket(self, event_id, participant_id):
        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")

        result = self.ticket_service.process_new_ticket(participant_id, participant)
        if result.get("success"):
            return {"message": "Ticket inviato con successo"}
        raise ExternalServiceError(result.get("error", "Errore durante l'invio"))

    def check_participants(self, event_id: str, participants: list):
        if not event_id or not isinstance(participants, list) or not participants:
            raise ValidationError("eventId o participants mancanti")

        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        purchase_mode = event_model.purchase_mode or EventPurchaseAccessType.PUBLIC

        normalized_participants: List[CheckoutParticipantDTO] = []
        for entry in participants:
            if isinstance(entry, CheckoutParticipantDTO):
                normalized_participants.append(entry)
            elif isinstance(entry, dict):
                normalized_participants.append(CheckoutParticipantDTO.from_payload(entry))

        result = run_basic_checks(event_id, normalized_participants, event_model)
        if result.errors:
            err = ValidationError("validation_error")
            err.details = result.errors
            raise err

        if purchase_mode == EventPurchaseAccessType.ON_REQUEST:
            return {"valid": True, "members": result.members, "nonMembers": result.non_members}

        if purchase_mode == EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS and result.non_members:
            msg = (
                "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: "
                + ", ".join(result.non_members)
            )
            err = ValidationError("validation_error")
            err.details = [msg]
            raise err

        return {"valid": True}
