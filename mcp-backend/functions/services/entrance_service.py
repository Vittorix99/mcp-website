import logging
import secrets
from datetime import datetime, timedelta, timezone

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from errors.service_errors import NotFoundError, ValidationError
from repositories.event_repository import EventRepository


class EntranceService:
    def __init__(self):
        self.logger = logging.getLogger("EntranceService")
        self.event_repository = EventRepository()

    def _count_event_participants(self, event_id: str) -> int:
        if not event_id:
            return 0
        docs = (
            db.collection("participants")
            .document(event_id)
            .collection("participants_event")
            .stream()
        )
        return sum(1 for _ in docs)

    def _count_event_entered(self, event_id: str) -> int:
        if not event_id:
            return 0
        docs = (
            db.collection("entrance_scans")
            .document(event_id)
            .collection("scans")
            .stream()
        )
        return sum(1 for _ in docs)

    def _build_event_counts(self, event_id: str) -> dict:
        return {
            "participants_count": self._count_event_participants(event_id),
            "entered_count": self._count_event_entered(event_id),
        }

    def _get_scan_token_doc(self, scan_token: str):
        """Fetch and validate a scan token document. Raises ValidationError if invalid."""
        doc = db.collection("scan_tokens").document(scan_token).get()
        if not doc.exists:
            raise ValidationError("not_found")

        data = doc.to_dict() or {}

        if not data.get("is_active", False):
            raise ValidationError("inactive")

        expires_at = data.get("expires_at")
        if expires_at is not None:
            # expires_at may be a Firestore DatetimeWithNanoseconds or a plain datetime
            if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise ValidationError("expired")

        return data

    def generate_scan_token(self, event_id: str, admin_uid: str) -> dict:
        """Create a new scan token for the given event. Requires a valid event."""
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        token = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=12)

        db.collection("scan_tokens").document(token).set({
            "event_id": event_id,
            "created_by": admin_uid,
            "created_at": firestore.SERVER_TIMESTAMP,
            "expires_at": expires_at,
            "is_active": True,
        })

        self.logger.info("Scan token generato: %s per evento %s da %s", token, event_id, admin_uid)

        return {
            "token": token,
            "scan_url": f"https://musiconnectingpeople.com/scan/{token}",
        }

    def deactivate_scan_token(self, token: str) -> None:
        """Disattiva un token di scansione impostando is_active=False."""
        doc_ref = db.collection("scan_tokens").document(token)
        doc = doc_ref.get()
        if not doc.exists:
            raise NotFoundError("Token non trovato")
        doc_ref.update({"is_active": False})
        self.logger.info("Scan token disattivato: %s", token)

    def verify_scan_token(self, token: str) -> dict:
        """Verify a scan token and return event info if valid."""
        token = (token or "").strip()
        try:
            token_data = self._get_scan_token_doc(token)
        except ValidationError as err:
            return {"valid": False, "reason": str(err)}

        event_id = token_data.get("event_id", "")
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

        event_id = token_data.get("event_id", "")

        # Step 2 — verifica che la tessera esista e sia attiva (non scaduta/invalidata).
        # Questo blocca screenshot di QR di anni precedenti: il membership_id non cambia
        # ma subscription_valid viene azzerato a fine anno per tutte le tessere scadute.
        membership_doc = db.collection("memberships").document(membership_id).get()
        if not membership_doc.exists:
            self.logger.info("validate_entry: membership non trovata — %s", membership_id)
            return {
                "result": "invalid_member_not_found",
                "membership": None,
                "scanned_at": None,
            }

        membership_data = membership_doc.to_dict() or {}
        if not membership_data.get("subscription_valid", False):
            member_info = {
                "name": membership_data.get("name", ""),
                "surname": membership_data.get("surname", ""),
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
        # Usa collection_group per sfruttare l'indice COLLECTION_GROUP già esistente
        # su membershipId, poi filtra lato Python sull'event_id corretto.
        all_participant_docs = (
            db.collection_group("participants_event")
            .where(filter=FieldFilter("membershipId", "==", membership_id))
            .get()
        )
        participant_docs = [
            doc for doc in all_participant_docs
            if doc.reference.parent.parent.id == event_id
        ]

        if not participant_docs:
            self.logger.info(
                "validate_entry: nessun acquisto trovato — membership %s evento %s",
                membership_id, event_id,
            )
            member_info = {
                "name": membership_data.get("name", ""),
                "surname": membership_data.get("surname", ""),
            }
            return {
                "result": "invalid_no_purchase",
                "membership": member_info,
                "scanned_at": None,
            }

        participant_data = participant_docs[0].to_dict() or {}
        member_info = {
            "name": participant_data.get("name", ""),
            "surname": participant_data.get("surname", ""),
        }
        counts = self._build_event_counts(event_id)

        # Step 4 — verifica se già entrato
        scan_ref = (
            db.collection("entrance_scans")
            .document(event_id)
            .collection("scans")
            .document(membership_id)
        )
        existing_scan = scan_ref.get()
        if existing_scan.exists:
            existing_data = existing_scan.to_dict() or {}
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

        # Step 5 — scrivi ingresso
        scan_ref.set({
            "scanned_at": firestore.SERVER_TIMESTAMP,
            "scan_token": scan_token,
        })

        # Aggiorna il campo display sul partecipante
        participant_docs[0].reference.update({
            "entered": True,
            "entered_at": firestore.SERVER_TIMESTAMP,
        })
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
        all_docs = (
            db.collection_group("participants_event")
            .where(filter=FieldFilter("membershipId", "==", membership_id))
            .get()
        )
        participant_docs = [
            doc for doc in all_docs
            if doc.reference.parent.parent.id == event_id
        ]

        if not participant_docs:
            raise NotFoundError("Partecipante non trovato per questa tessera in questo evento")

        participant_ref = participant_docs[0].reference
        scan_ref = (
            db.collection("entrance_scans")
            .document(event_id)
            .collection("scans")
            .document(membership_id)
        )

        if entered:
            if scan_ref.get().exists:
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

            scan_ref.set({
                "scanned_at": firestore.SERVER_TIMESTAMP,
                "manual": True,
                "operator": admin_uid,
            })
            participant_ref.update({
                "entered": True,
                "entered_at": firestore.SERVER_TIMESTAMP,
            })
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
            scan_ref.delete()
            participant_ref.update({
                "entered": False,
                "entered_at": None,
            })
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

        ref = db.collection("scan_tokens").document(token)
        snap = ref.get()
        if not snap.exists:
            raise NotFoundError("Scan token non trovato")

        data = snap.to_dict() or {}
        was_active = bool(data.get("is_active", False))
        event_id = data.get("event_id", "")

        ref.update({
            "is_active": False,
            "deactivated_by": admin_uid,
            "deactivated_at": firestore.SERVER_TIMESTAMP,
        })

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
        try:
            doc = db.collection("memberships").document(membership_id).get()
            if doc.exists:
                data = doc.to_dict() or {}
                return {"name": data.get("name", ""), "surname": data.get("surname", "")}
        except Exception:
            pass
        return {"name": "", "surname": ""}
