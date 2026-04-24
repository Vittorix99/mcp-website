import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from errors.service_errors import NotFoundError, ValidationError
from interfaces.repositories import EventRepositoryProtocol
from models.scan_token import ScanToken
from repositories.entrance_scan_repository import EntranceScanRepository
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from repositories.scan_token_repository import ScanTokenRepository


class EntranceService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        scan_token_repository: Optional[ScanTokenRepository] = None,
        entrance_scan_repository: Optional[EntranceScanRepository] = None,
        participant_repository: Optional[ParticipantRepository] = None,
        membership_repository: Optional[MembershipRepository] = None,
    ):
        self.logger = logging.getLogger("EntranceService")
        self.event_repository = event_repository or EventRepository()
        self.scan_token_repository = scan_token_repository or ScanTokenRepository()
        self.entrance_scan_repository = entrance_scan_repository or EntranceScanRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.membership_repository = membership_repository or MembershipRepository()

    def _build_event_counts(self, event_id: str) -> dict:
        return {
            "participants_count": self.participant_repository.count(event_id),
            "entered_count": self.entrance_scan_repository.count(event_id),
        }

    def _get_scan_token_doc(self, scan_token: str) -> ScanToken:
        """Fetch and validate a scan token document. Raises ValidationError if invalid."""
        token = self.scan_token_repository.get(scan_token)
        if token is None:
            raise ValidationError("not_found")

        if not token.is_active:
            raise ValidationError("inactive")

        expires_at = token.expires_at
        if expires_at is not None:
            # expires_at may be a Firestore DatetimeWithNanoseconds or a plain datetime
            if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise ValidationError("expired")

        return token

    def generate_scan_token(self, event_id: str, admin_uid: str) -> dict:
        """Create a new scan token for the given event. Requires a valid event."""
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        token = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=12)

        self.scan_token_repository.create(token, event_id, admin_uid, expires_at)
        self.logger.info("Scan token generato: %s per evento %s da %s", token, event_id, admin_uid)

        return {
            "token": token,
            "scan_url": f"https://musiconnectingpeople.com/scan/{token}",
        }

    def verify_scan_token(self, token: str) -> dict:
        """Verify a scan token and return event info if valid."""
        token = (token or "").strip()
        try:
            token_data = self._get_scan_token_doc(token)
        except ValidationError as err:
            return {"valid": False, "reason": str(err)}

        event_id = token_data.event_id
        event_model = self.event_repository.get_model(event_id)
        event_title = event_model.title if event_model else ""
        counts = self._build_event_counts(event_id)

        self.logger.info("Scan token verificato: %s — evento %s", token, event_id)

        return {
            "valid": True,
            "event_id": event_id,
            "event_title": event_title,
            "participants_count": counts["participants_count"],
            "entered_count": counts["entered_count"],
        }

    def validate_entry(self, membership_id: str, scan_token: str) -> dict:
        """
        Validate a membership QR scan at event entrance.

        Returns a unified response dict with keys:
          result, membership (name/surname), scanned_at
        """
        membership_id = (membership_id or "").strip()
        scan_token = (scan_token or "").strip()

        # Step 1 — verifica scan token
        try:
            token_data = self._get_scan_token_doc(scan_token)
        except ValidationError:
            self.logger.warning("validate_entry: scan token non valido — %s", scan_token)
            return {
                "result": "invalid_token",
                "membership": None,
                "scanned_at": None,
            }

        event_id = token_data.event_id

        # Step 2 — verifica che la tessera esista e sia attiva (non scaduta/invalidata).
        # Questo blocca screenshot di QR di anni precedenti: il membership_id non cambia
        # ma subscription_valid viene azzerato a fine anno per tutte le tessere scadute.
        membership_member = self.membership_repository.get(membership_id)
        if membership_member is None:
            self.logger.info("validate_entry: membership non trovata — %s", membership_id)
            return {
                "result": "invalid_member_not_found",
                "membership": None,
                "scanned_at": None,
            }

        if not membership_member.subscription_valid:
            member_info = {
                "name": membership_member.name,
                "surname": membership_member.surname,
            }
            self.logger.info(
                "validate_entry: tessera non valida (subscription_valid=False) — membership %s",
                membership_id,
            )
            return {
                "result": "invalid_membership",
                "membership": member_info,
                "scanned_at": None,
            }

        # Step 3 — verifica che la membership abbia un acquisto per questo evento.
        participant_model = self.participant_repository.get_by_membership_id(event_id, membership_id)
        if participant_model is None:
            self.logger.info(
                "validate_entry: nessun acquisto trovato — membership %s evento %s",
                membership_id, event_id,
            )
            member_info = {
                "name": membership_member.name,
                "surname": membership_member.surname,
            }
            return {
                "result": "invalid_no_purchase",
                "membership": member_info,
                "scanned_at": None,
            }

        member_info = {
            "name": participant_model.name,
            "surname": participant_model.surname,
        }
        counts = self._build_event_counts(event_id)

        # Step 4 — fast-path: se il documento scan esiste già, return immediato
        existing_data = self.entrance_scan_repository.get(event_id, membership_id)
        if existing_data is not None:
            scanned_at = existing_data.get("scanned_at")
            scanned_at_iso = scanned_at.isoformat() if scanned_at and hasattr(scanned_at, "isoformat") else None
            self.logger.info(
                "validate_entry: già scansionato — membership %s evento %s",
                membership_id, event_id,
            )
            return {
                "result": "already_scanned",
                "membership": member_info,
                "scanned_at": scanned_at_iso,
                "participants_count": counts["participants_count"],
                "entered_count": counts["entered_count"],
            }

        # Step 5 — scrivi ingresso con create() atomico.
        # Se due richieste concorrenti superano il fast-path (Step 4), solo una
        # delle due avrà successo qui: create_scan() ritorna i dati esistenti se
        # AlreadyExists, None se il documento è stato creato con successo.
        race_data = self.entrance_scan_repository.create_scan(event_id, membership_id, scan_token)
        if race_data is not None:
            scanned_at = race_data.get("scanned_at")
            scanned_at_iso = scanned_at.isoformat() if scanned_at and hasattr(scanned_at, "isoformat") else None
            self.logger.info(
                "validate_entry: race condition risolta — membership %s già registrata",
                membership_id,
            )
            return {
                "result": "already_scanned",
                "membership": member_info,
                "scanned_at": scanned_at_iso,
                "participants_count": counts["participants_count"],
                "entered_count": counts["entered_count"],
            }

        # Aggiorna il campo entered sul partecipante
        self.participant_repository.update_entered(event_id, participant_model.id, entered=True)
        counts = self._build_event_counts(event_id)

        self.logger.info(
            "validate_entry: ingresso registrato — membership %s evento %s token %s",
            membership_id, event_id, scan_token,
        )

        return {
            "result": "valid",
            "membership": member_info,
            "scanned_at": None,
            "participants_count": counts["participants_count"],
            "entered_count": counts["entered_count"],
        }

    def manual_entry(self, event_id: str, membership_id: str, entered: bool, admin_uid: str) -> dict:
        """Segna manualmente l'entrata o l'uscita di un membro (solo admin)."""
        event_id = (event_id or "").strip()
        membership_id = (membership_id or "").strip()

        participant_model = self.participant_repository.get_by_membership_id(event_id, membership_id)
        if participant_model is None:
            raise NotFoundError("Partecipante non trovato per questa tessera in questo evento")

        if entered:
            if self.entrance_scan_repository.exists(event_id, membership_id):
                self.logger.info(
                    "manual_entry: già entrato — membership %s evento %s",
                    membership_id, event_id,
                )
                counts = self._build_event_counts(event_id)
                return {
                    "result": "already_entered",
                    "participants_count": counts["participants_count"],
                    "entered_count": counts["entered_count"],
                }

            self.entrance_scan_repository.create_manual(event_id, membership_id, admin_uid)
            self.participant_repository.update_entered(event_id, participant_model.id, entered=True)
            self.logger.info(
                "manual_entry: ingresso manuale registrato — membership %s evento %s operatore %s",
                membership_id, event_id, admin_uid,
            )
            counts = self._build_event_counts(event_id)
            return {
                "result": "entered",
                "participants_count": counts["participants_count"],
                "entered_count": counts["entered_count"],
            }
        else:
            self.entrance_scan_repository.delete(event_id, membership_id)
            self.participant_repository.update_entered(event_id, participant_model.id, entered=False)
            self.logger.info(
                "manual_entry: ingresso annullato — membership %s evento %s operatore %s",
                membership_id, event_id, admin_uid,
            )
            counts = self._build_event_counts(event_id)
            return {
                "result": "undone",
                "participants_count": counts["participants_count"],
                "entered_count": counts["entered_count"],
            }

    def deactivate_scan_token(self, token: str, admin_uid: str) -> dict:
        token = (token or "").strip()
        if not token:
            raise ValidationError("token_required")

        token_model = self.scan_token_repository.get(token)
        if token_model is None:
            raise NotFoundError("Scan token non trovato")

        was_active = token_model.is_active
        event_id = token_model.event_id

        self.scan_token_repository.deactivate(token, admin_uid)

        self.logger.info(
            "Scan token disattivato: %s (event=%s, by=%s, was_active=%s)",
            token,
            event_id,
            admin_uid,
            was_active,
        )
        return {
            "ok": True,
            "token": token,
            "event_id": event_id,
            "is_active": False,
            "already_inactive": (not was_active),
        }

    def _get_member_info(self, membership_id: str) -> dict:
        """Fetch name/surname from memberships collection, returns empty strings if not found."""
        member = self.membership_repository.get(membership_id)
        if member:
            return {"name": member.name, "surname": member.surname}
        return {"name": "", "surname": ""}
