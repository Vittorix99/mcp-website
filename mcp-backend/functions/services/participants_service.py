import logging
from datetime import datetime, timezone

from flask import jsonify
from google.cloud import firestore

from config.firebase_config import db
from models import EventParticipant, EventPurchaseAccessType, Membership
from services.ticket_service import process_new_ticket
from utils.events_utils import calculate_end_of_year_membership, is_minor
from utils.participant_rules import run_basic_checks


class ParticipantsService:
    def __init__(self):
        self.logger = logging.getLogger("ParticipantsService")
        self.collection_name = "participants"
        self.db = db

    def _get_collection(self, event_id):
        return self.db.collection(f"{self.collection_name}/{event_id}/participants_event")

    def _participant_from_snapshot(self, snapshot, event_id) -> EventParticipant:
        participant = EventParticipant.from_firestore(snapshot.to_dict() or {}, snapshot.id)
        participant.event_id = participant.event_id or event_id
        return participant

    def _serialize(self, participant: EventParticipant):
        payload = participant.to_firestore(include_none=True)
        payload["id"] = participant.id
        return payload

    def _apply_updates(self, participant: EventParticipant, updates: dict):
        mapping = {
            "name": "name",
            "surname": "surname",
            "email": "email",
            "phone": "phone",
            "birthdate": "birthdate",
            "membershipId": "membership_id",
            "membership_id": "membership_id",
            "membership_included": "membership_included",
            "membershipIncluded": "membership_included",
            "ticket_sent": "ticket_sent",
            "ticketSent": "ticket_sent",
            "location_sent": "location_sent",
            "locationSent": "location_sent",
            "newsletterConsent": "newsletter_consent",
            "newsletter_consent": "newsletter_consent",
            "price": "price",
        }

        for key, value in updates.items():
            attr = mapping.get(key, key)
            if hasattr(participant, attr):
                setattr(participant, attr, value)

    def get_all(self, event_id):
        try:
            docs = self._get_collection(event_id).stream()
            participants = [self._serialize(self._participant_from_snapshot(doc, event_id)) for doc in docs]
            return jsonify(participants), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {"error": str(e)}, 500

    def get_by_id(self, event_id, participant_id):
        try:
            ref = self._get_collection(event_id).document(participant_id)
            doc = ref.get()
            if not doc.exists:
                return {"error": "Participant not found"}, 404

            participant = self._participant_from_snapshot(doc, event_id)
            return jsonify(self._serialize(participant)), 200
        except Exception as e:
            self.logger.error(f"[get_by_id] {e}")
            return {"error": str(e)}, 500

    def create(self, participant_data):
        try:
            event_id = participant_data.get("event_id")
            if not event_id:
                return {"error": "event_id is required"}, 400

            birthdate = participant_data.get("birthdate")
            if not birthdate or is_minor(birthdate):
                return {"error": "Partecipante minorenne non consentito"}, 403

            email = participant_data.get("email", "").lower().strip()
            phone = participant_data.get("phone", "").strip()
            membership_included = participant_data.get("membership_included", False)

            membership_id = None
            is_member = False

            existing = (
                self.db.collection("memberships")
                .where("subscription_valid", "==", True)
                .where("email", "==", email)
                .get()
            )

            if not existing and phone:
                existing = (
                    self.db.collection("memberships")
                    .where("subscription_valid", "==", True)
                    .where("phone", "==", phone)
                    .get()
                )

            if existing:
                is_member = True
                membership_id = existing[0].id

            if membership_included and is_member:
                return {"error": "Questo utente è già un membro attivo"}, 409

            if membership_included and not is_member:
                now = datetime.now(timezone.utc)
                end_date = calculate_end_of_year_membership(now)

                membership = Membership(
                    name=participant_data.get("name", ""),
                    surname=participant_data.get("surname", ""),
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

                ref = self.db.collection("memberships").add(membership.to_firestore(include_none=True))[1]
                membership_id = ref.id
                self.logger.info(f"✅ Nuova membership creata: {membership_id}")

            event_doc = self.db.collection("events").document(event_id).get()
            if not event_doc.exists:
                return {"error": "Evento non trovato"}, 404

            event_type = event_doc.to_dict().get("type", "")
            if event_type == "community" and not (membership_id or is_member):
                return {"error": "Per eventi community è richiesta la membership attiva"}, 403

            participant = EventParticipant(
                event_id=event_id,
                name=participant_data.get("name", ""),
                surname=participant_data.get("surname", ""),
                email=email,
                phone=phone,
                birthdate=birthdate,
                membership_included=bool(membership_id or membership_included),
                membership_id=membership_id,
                ticket_sent=participant_data.get("ticket_sent", False),
                location_sent=participant_data.get("location_sent", False),
                newsletter_consent=participant_data.get("newsletterConsent", False),
                price=participant_data.get("price"),
                purchase_id=participant_data.get("purchase_id"),
                created_at=firestore.SERVER_TIMESTAMP,
            )

            doc_ref = self._get_collection(event_id).add(participant.to_firestore(include_none=True))
            participant_id = doc_ref[1].id
            self.logger.info(f"👤 Partecipante creato: {participant_id}")

            if membership_id:
                self.db.collection("memberships").document(membership_id).update(
                    {"attended_events": firestore.ArrayUnion([event_id])}
                )

            return jsonify({"message": "Participant created", "id": participant_id}), 201

        except Exception as e:
            self.logger.error(f"[create] {e}")
            return {"error": str(e)}, 500

    def update(self, event_id, participant_id, data):
        try:
            doc_ref = self._get_collection(event_id).document(participant_id)
            snapshot = doc_ref.get()
            if not snapshot.exists:
                return jsonify({"error": "Participant not found"}), 404

            participant = self._participant_from_snapshot(snapshot, event_id)

            if participant.purchase_id and "price" in data:
                return jsonify({"error": "Modifica del prezzo non permessa: purchase già registrato"}), 400

            if participant.purchase_id and "price" in data:
                data.pop("price", None)

            self._apply_updates(participant, data)
            doc_ref.set(participant.to_firestore(include_none=True))
            return jsonify({"message": "Participant updated"}), 200

        except Exception as e:
            self.logger.error(f"[update] {e}")
            return {"error": str(e)}, 500

    def delete(self, event_id, participant_id):
        try:
            self._get_collection(event_id).document(participant_id).delete()
            return jsonify({"message": "Participant deleted"}), 200
        except Exception as e:
            self.logger.error(f"[delete] {e}")
            return {"error": str(e)}, 500

    def send_ticket(self, event_id, participant_id):
        try:
            doc_ref = self._get_collection(event_id).document(participant_id)
            doc = doc_ref.get()

            if not doc.exists:
                return {"error": "Participant not found"}, 404

            participant = self._participant_from_snapshot(doc, event_id)
            result = process_new_ticket(participant_id, self._serialize(participant))

            if result.get("success"):
                return jsonify({"message": "Ticket inviato con successo"}), 200
            return {"error": result.get("error", "Errore durante l'invio")}, 500

        except Exception as e:
            self.logger.error(f"[send_ticket] {e}")
            return {"error": str(e)}, 500

    def check_participants(self, event_id: str, participants: list):
        try:
            if not event_id or not isinstance(participants, list) or not participants:
                return jsonify({"error": "eventId o participants mancanti"}), 400

            event_doc = self.db.collection("events").document(event_id).get()
            if not event_doc.exists:
                return jsonify({"error": "Evento non trovato"}), 404
            event_data = event_doc.to_dict() or {}

            purchase_mode_raw = (event_data.get("type") or "").upper()
            try:
                purchase_mode = EventPurchaseAccessType(purchase_mode_raw)
            except Exception:
                purchase_mode = EventPurchaseAccessType.PUBLIC

            result = run_basic_checks(event_id, participants, event_data)
            if result.errors:
                return jsonify({"valid": False, "errors": result.errors}), 400

            if purchase_mode == EventPurchaseAccessType.ON_REQUEST:
                return (
                    jsonify({"valid": True, "members": result.members, "nonMembers": result.non_members}),
                    200,
                )

            if purchase_mode == EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS and result.non_members:
                msg = (
                    "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: "
                    + ", ".join(result.non_members)
                )
                return jsonify({"valid": False, "errors": [msg]}), 400

            return jsonify({"valid": True}), 200

        except Exception as e:
            self.logger.error(f"[check_participants] {e}")
            return jsonify({"error": "Internal server error"}), 500
