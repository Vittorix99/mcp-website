import logging
from flask import jsonify
from config.firebase_config import db
from utils.events_utils import is_minor  # Deve restituire True se minorenne
from google.cloud import firestore
from utils.events_utils import is_minor, calculate_end_of_year, calculate_end_of_year_membership
from services.ticket_service import process_new_ticket
from datetime import datetime, timezone

from datetime import datetime, timezone

class ParticipantsService:
    def __init__(self):
        self.logger = logging.getLogger("ParticipantsService")
        self.collection_name = "participants"
        self.db = db

    def _get_collection(self, event_id):
        return db.collection(f'{self.collection_name}/{event_id}/participants_event')

    def get_all(self, event_id):
        try:
            docs = self._get_collection(event_id).stream()
            participants = [{**doc.to_dict(), 'id': doc.id} for doc in docs]
            return jsonify(participants), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {'error': str(e)}, 500

    def get_by_id(self, event_id, participant_id):
        try:
            ref = self._get_collection(event_id).document(participant_id)
            doc = ref.get()
            if not doc.exists:
                return {'error': 'Participant not found'}, 404

            return jsonify({**doc.to_dict(), 'id': doc.id}), 200
        except Exception as e:
            self.logger.error(f"[get_by_id] {e}")
            return {'error': str(e)}, 500

    def create(self, participant_data):
        try:
            print("Participant Data is:", participant_data)
            event_id = participant_data.get('event_id')
            if not event_id:
                return {'error': 'event_id is required'}, 400

            birthdate = participant_data.get('birthdate')
            if not birthdate or is_minor(birthdate):
                return {'error': 'Partecipante minorenne non consentito'}, 403

            email = participant_data.get("email", "").lower().strip()
            phone = participant_data.get("phone", "").strip()
            membership_included = participant_data.get("membership_included", False)

            membership_id = None
            is_member = False

            # 🔍 Cerca membership esistente
            existing = self.db.collection("memberships") \
                .where("subscription_valid", "==", True) \
                .where("email", "==", email).get()

            if not existing and phone:
                existing = self.db.collection("memberships") \
                    .where("subscription_valid", "==", True) \
                    .where("phone", "==", phone).get()

            if existing:
                is_member = True
                membership_id = existing[0].id

            # 🚫 Già membro ma vuole includere membership → errore
            if membership_included and is_member:
                return {'error': 'Questo utente è già un membro attivo'}, 409

            # ✅ Se vuole membership ma non è ancora membro
            if membership_included and not is_member:
                now = datetime.now(timezone.utc)
                end_date = calculate_end_of_year_membership(now)

                membership_data = {
                    "name": participant_data.get("name"),
                    "surname": participant_data.get("surname"),
                    "email": email,
                    "phone": phone,
                    "birthdate": birthdate,
                    "start_date": now.isoformat(),
                    "end_date": end_date,
                    "subscription_valid": True,
                    "membership_sent": False,
                    "membership_type": "manual",
                    "purchase_id": None
                }

                ref = self.db.collection("memberships").add(membership_data)[1]
                membership_id = ref.id
                self.logger.info(f"✅ Nuova membership creata: {membership_id}")

            # 📄 Verifica tipo evento
            event_doc = self.db.collection("events").document(event_id).get()
            if not event_doc.exists:
                return {'error': 'Evento non trovato'}, 404

            event_type = event_doc.to_dict().get("type", "")
            if event_type == "community" and not (membership_id or is_member):
                return {'error': 'Per eventi community è richiesta la membership attiva'}, 403

            # 🕒 Timestamp
            participant_data["createdAt"] = firestore.SERVER_TIMESTAMP
            if membership_id:
                participant_data["membershipId"] = membership_id

            # 🔖 Salva partecipante
            doc_ref = self._get_collection(event_id).add(participant_data)
            participant_id = doc_ref[1].id
            self.logger.info(f"👤 Partecipante creato: {participant_id}")

            # 📌 Aggiungi evento alla membership (se esiste)
            if membership_id:
                self.db.collection("memberships").document(membership_id).update({
                    "attended_events": firestore.ArrayUnion([event_id])
                })

            return jsonify({'message': 'Participant created', 'id': participant_id}), 201

        except Exception as e:
            self.logger.error(f"[create] {e}")
            return {'error': str(e)}, 500

    def update(self, event_id, participant_id, data):
        try:
            doc_ref = self._get_collection(event_id).document(participant_id)
            snapshot = doc_ref.get()
            if not snapshot.exists:
                return jsonify({'error': 'Participant not found'}), 404

            existing = snapshot.to_dict() or {}

            # Se il partecipante ha già un purchase_id, non permettere l'aggiornamento del prezzo
            if 'purchase_id' in existing and 'price' in data:
                return jsonify({'error': 'Modifica del prezzo non permessa: purchase già registrato'}), 400

            # Rimuovo price da data se già presente erroneamente
            if 'purchase_id' in existing and 'price' in data:
                data.pop('price', None)

            # Procedo con l'aggiornamento dei campi ammessi
            doc_ref.update(data)

            return jsonify({'message': 'Participant updated'}), 200

        except Exception as e:
            self.logger.error(f"[update] {e}")
            return {'error': str(e)}, 500

    def delete(self, event_id, participant_id):
        try:
            self._get_collection(event_id).document(participant_id).delete()
            return jsonify({'message': 'Participant deleted'}), 200
        except Exception as e:
            self.logger.error(f"[delete] {e}")
            return {'error': str(e)}, 500

    def send_ticket(self, event_id, participant_id):
        try:
            doc_ref = self._get_collection(event_id).document(participant_id)
            doc = doc_ref.get()

            if not doc.exists:
                return {"error": "Participant not found"}, 404

            participant_data = doc.to_dict()
            result = process_new_ticket(participant_id, participant_data)

            if result.get("success"):
                return jsonify({"message": "Ticket inviato con successo"}), 200
            else:
                return {"error": result.get("error", "Errore durante l'invio")}, 500

        except Exception as e:
            self.logger.error(f"[send_ticket] {e}")
            return {"error": str(e)}, 500

    def send_location(self, participant_id):
        self.logger.warning("send_location not implemented yet")
        return {'error': 'Not implemented'}, 501