from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from errors.service_errors import NotFoundError, ValidationError
from interfaces.repositories import (
    EntranceScanRepositoryProtocol,
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    ParticipantRepositoryProtocol,
    ScanTokenRepositoryProtocol,
)
from dto.entrance_api import (
    DeactivateScanTokenRequestDTO,
    DeactivateScanTokenResponseDTO,
    GenerateScanTokenRequestDTO,
    GenerateScanTokenResponseDTO,
    ManualEntryRequestDTO,
    ManualEntryResponseDTO,
    MemberInfoDTO,
    ValidateEntryRequestDTO,
    ValidateEntryResponseDTO,
    VerifyScanTokenQueryDTO,
    VerifyScanTokenResponseDTO,
)
from config.external_services import SCAN_BASE_URL
from models.scan_token import ScanToken
from repositories.entrance_scan_repository import EntranceScanRepository
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from repositories.scan_token_repository import ScanTokenRepository
from utils.safe_logging import safe_id


class EntranceService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        scan_token_repository: Optional[ScanTokenRepositoryProtocol] = None,
        entrance_scan_repository: Optional[EntranceScanRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
    ):
        self.logger = logging.getLogger("EntranceService")
        self.event_repository = event_repository or EventRepository()
        self.scan_token_repository = scan_token_repository or ScanTokenRepository()
        self.entrance_scan_repository = entrance_scan_repository or EntranceScanRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.membership_repository = membership_repository or MembershipRepository()

    def _build_event_counts(self, event_id: str) -> dict:
        # I conteggi vengono ricalcolati dopo ogni mutazione per dare feedback live allo scanner.
        return {
            "participants_count": self.participant_repository.count(event_id),
            "entered_count": self.entrance_scan_repository.count(event_id),
        }

    def _get_scan_token_doc(self, scan_token: str) -> ScanToken:
        # Il token non autorizza l'ingresso da solo: serve solo a legare lo scanner a un evento.
        token = self.scan_token_repository.get(scan_token)
        if token is None:
            raise ValidationError("not_found")
        if not token.is_active:
            raise ValidationError("inactive")
        expires_at = token.expires_at
        if expires_at is not None:
            if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise ValidationError("expired")
        return token

    def generate_scan_token(
        self, dto: GenerateScanTokenRequestDTO, admin_uid: str
    ) -> GenerateScanTokenResponseDTO:
        event_model = self.event_repository.get_model(dto.event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        # Token opaco e temporaneo: l'URL pubblico non espone l'id evento direttamente.
        token = secrets.token_hex(16)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        self.scan_token_repository.create(token, dto.event_id, admin_uid, expires_at)
        self.logger.info("Scan token generato per evento %s da admin %s", dto.event_id, safe_id(admin_uid))

        return GenerateScanTokenResponseDTO(
            token=token,
            scan_url=f"{SCAN_BASE_URL}/scan/{token}",
        )

    def verify_scan_token(self, dto: VerifyScanTokenQueryDTO) -> VerifyScanTokenResponseDTO:
        try:
            token_data = self._get_scan_token_doc(dto.token)
        except ValidationError as err:
            return VerifyScanTokenResponseDTO(valid=False, reason=str(err))

        event_id = token_data.event_id
        event_model = self.event_repository.get_model(event_id)
        event_title = event_model.title if event_model else ""
        counts = self._build_event_counts(event_id)

        self.logger.info("Scan token verificato: token=%s evento=%s", safe_id(dto.token), event_id)

        return VerifyScanTokenResponseDTO(
            valid=True,
            event_id=event_id,
            event_title=event_title,
            participants_count=counts["participants_count"],
            entered_count=counts["entered_count"],
        )

    def validate_entry(self, dto: ValidateEntryRequestDTO) -> ValidateEntryResponseDTO:
        # Step 1: verifica scan token e recupera l'evento associato allo scanner.
        try:
            token_data = self._get_scan_token_doc(dto.scan_token)
        except ValidationError:
            self.logger.warning("validate_entry: scan token non valido token=%s", safe_id(dto.scan_token))
            return ValidateEntryResponseDTO(result="invalid_token")

        event_id = token_data.event_id

        # Step 2: verifica che la tessera esista e sia attiva.
        # Questo blocca i QR vecchi quando il trigger di inizio anno invalida le membership.
        membership_member = self.membership_repository.get(dto.membership_id)
        if membership_member is None:
            self.logger.info("validate_entry: membership non trovata — %s", dto.membership_id)
            return ValidateEntryResponseDTO(result="invalid_member_not_found")

        if not membership_member.subscription_valid:
            self.logger.info(
                "validate_entry: tessera non valida (subscription_valid=False) — %s", dto.membership_id
            )
            return ValidateEntryResponseDTO(
                result="invalid_membership",
                membership=MemberInfoDTO(name=membership_member.name, surname=membership_member.surname),
            )

        # Step 3: la tessera e' valida solo se associata a un partecipante di questo evento.
        participant_model = self.participant_repository.get_by_membership_id(event_id, dto.membership_id)
        if participant_model is None:
            self.logger.info(
                "validate_entry: nessun acquisto — membership %s evento %s", dto.membership_id, event_id
            )
            return ValidateEntryResponseDTO(
                result="invalid_no_purchase",
                membership=MemberInfoDTO(name=membership_member.name, surname=membership_member.surname),
            )

        member_info = MemberInfoDTO(name=participant_model.name, surname=participant_model.surname)
        counts = self._build_event_counts(event_id)

        # Step 4: fast-path per doppia scansione gia' persistita.
        existing_scan = self.entrance_scan_repository.get(event_id, dto.membership_id)
        if existing_scan is not None:
            scanned_at = existing_scan.scanned_at
            scanned_at_iso = scanned_at.isoformat() if scanned_at and hasattr(scanned_at, "isoformat") else None
            self.logger.info("validate_entry: già scansionato — %s evento %s", dto.membership_id, event_id)
            return ValidateEntryResponseDTO(
                result="already_scanned",
                membership=member_info,
                scanned_at=scanned_at_iso,
                participants_count=counts["participants_count"],
                entered_count=counts["entered_count"],
            )

        # Step 5: scrittura atomica; se due scanner leggono insieme, uno solo crea il record.
        race_scan = self.entrance_scan_repository.create_scan(event_id, dto.membership_id, dto.scan_token)
        if race_scan is not None:
            scanned_at = race_scan.scanned_at
            scanned_at_iso = scanned_at.isoformat() if scanned_at and hasattr(scanned_at, "isoformat") else None
            self.logger.info("validate_entry: race condition risolta — %s", dto.membership_id)
            return ValidateEntryResponseDTO(
                result="already_scanned",
                membership=member_info,
                scanned_at=scanned_at_iso,
                participants_count=counts["participants_count"],
                entered_count=counts["entered_count"],
            )

        # Lo scan e' la fonte anti-doppio-ingresso; il flag sul participant serve alla UI/admin.
        self.participant_repository.update_entered(event_id, participant_model.id, entered=True)
        counts = self._build_event_counts(event_id)
        self.logger.info(
            "validate_entry: ingresso registrato membership=%s evento=%s token=%s",
            safe_id(dto.membership_id), event_id, safe_id(dto.scan_token),
        )

        return ValidateEntryResponseDTO(
            result="valid",
            membership=member_info,
            participants_count=counts["participants_count"],
            entered_count=counts["entered_count"],
        )

    def manual_entry(
        self, dto: ManualEntryRequestDTO, admin_uid: str
    ) -> ManualEntryResponseDTO:
        participant_model = self.participant_repository.get_by_membership_id(
            dto.event_id, dto.membership_id
        )
        if participant_model is None:
            raise NotFoundError("Partecipante non trovato per questa tessera in questo evento")

        counts = self._build_event_counts(dto.event_id)

        if dto.entered:
            # Entrata manuale: stessa sorgente dati dello scanner, ma marcata con operatore admin.
            if self.entrance_scan_repository.exists(dto.event_id, dto.membership_id):
                self.logger.info("manual_entry: già entrato — %s evento %s", dto.membership_id, dto.event_id)
                return ManualEntryResponseDTO(
                    result="already_entered",
                    participants_count=counts["participants_count"],
                    entered_count=counts["entered_count"],
                )
            self.entrance_scan_repository.create_manual(dto.event_id, dto.membership_id, admin_uid)
            self.participant_repository.update_entered(dto.event_id, participant_model.id, entered=True)
            self.logger.info(
                "manual_entry: ingresso manuale membership=%s evento=%s operatore=%s",
                safe_id(dto.membership_id), dto.event_id, safe_id(admin_uid),
            )
            counts = self._build_event_counts(dto.event_id)
            return ManualEntryResponseDTO(
                result="entered",
                participants_count=counts["participants_count"],
                entered_count=counts["entered_count"],
            )

        # Undo manuale: rimuove il record scan e riallinea il flag del partecipante.
        self.entrance_scan_repository.delete(dto.event_id, dto.membership_id)
        self.participant_repository.update_entered(dto.event_id, participant_model.id, entered=False)
        self.logger.info(
            "manual_entry: ingresso annullato membership=%s evento=%s operatore=%s",
            safe_id(dto.membership_id), dto.event_id, safe_id(admin_uid),
        )
        counts = self._build_event_counts(dto.event_id)
        return ManualEntryResponseDTO(
            result="undone",
            participants_count=counts["participants_count"],
            entered_count=counts["entered_count"],
        )

    def deactivate_scan_token(
        self, dto: DeactivateScanTokenRequestDTO, admin_uid: str
    ) -> DeactivateScanTokenResponseDTO:
        token_model = self.scan_token_repository.get(dto.token)
        if token_model is None:
            raise NotFoundError("Scan token non trovato")

        was_active = token_model.is_active
        event_id = token_model.event_id
        # Disattivare il token chiude lo scanner pubblico senza toccare gli scan gia' registrati.
        self.scan_token_repository.deactivate(dto.token, admin_uid)

        self.logger.info(
            "Scan token disattivato: token=%s event=%s by=%s was_active=%s",
            safe_id(dto.token), event_id, safe_id(admin_uid), was_active,
        )

        return DeactivateScanTokenResponseDTO(
            ok=True,
            token=dto.token,
            event_id=event_id,
            is_active=False,
            already_inactive=(not was_active),
        )
