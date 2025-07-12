# services/admin/memberships_service.py

from firebase_admin import firestore
from config.firebase_config import db, bucket
from flask import jsonify
from utils.events_utils import is_minor, calculate_end_of_year_membership
from datetime import datetime, timezone
import logging
from services.singup_service import process_new_membership, update_membership_card
from services.mail_service import gmail_send_email_template
from utils.email_templates import get_membership_email_template
from io import BytesIO


PROTECTED_FIELDS = ["card_storage_path", "purchase_id"]


class MembershipsService:
    def __init__(self):
        self.db = db
        self.collection = self.db.collection("memberships")
        self.logger = logging.getLogger("MembershipsService")
        self.storage = bucket
        self.settings_collection = self.db.collection("membership_settings")

    def get_all(self):
        try:
            docs = self.collection.stream()
            return jsonify([doc.to_dict() | {"id": doc.id} for doc in docs]), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {'error': str(e)}, 500

    def get_by_id(self, membership_id):
        try:
            doc = self.collection.document(membership_id).get()
            if not doc.exists:
                return {'error': 'Membership not found'}, 404
            return jsonify(doc.to_dict()), 200
        except Exception as e:
            self.logger.error(f"[get_by_id] {e}")
            return {'error': str(e)}, 500

    def create(self, data):
        try:
            if any(field in data for field in PROTECTED_FIELDS):
                return {'error': 'Modifica a campi riservati non consentita'}, 403

            birthdate = data.get("birthdate")
            if not birthdate or is_minor(birthdate):
                return {'error': 'Utente minorenne non ammesso'}, 403

            email = data.get("email")
            phone = data.get("phone")
            if not email and not phone:
                return {'error': 'Email o telefono obbligatorio'}, 400

            existing_query = self.collection.where("subscription_valid", "==", True)
            if email:
                existing_query = existing_query.where("email", "==", email)
            if phone:
                existing_query = existing_query.where("phone", "==", phone)

            existing = existing_query.get()
            if existing:
                return {'error': 'Utente già tesserato'}, 409

            now = datetime.now(timezone.utc)
            start_date = now.isoformat()
            end_date = calculate_end_of_year_membership(now)

            membership = {
                "name": data.get("name"),
                "surname": data.get("surname"),
                "email": email,
                "phone": phone,
                "birthdate": birthdate,
                "start_date": start_date,
                "end_date": end_date,
                "subscription_valid": True,
                "membership_sent": False,
                "membership_type": data.get("membership_type", "manual"),
                "purchase_id": None,
                "send_card_on_create": data.get("send_card_on_create", False)
                
            }

            ref = self.collection.add(membership)[1]
            self.logger.info(f"[create] Membership created with ID: {ref.id}")
            return jsonify({'message': 'Membership created', 'id': ref.id}), 201

        except Exception as e:
            self.logger.error(f"[create] {e}")
            return {'error': str(e)}, 500

    def update(self, membership_id, data):
        try:
            if any(field in data for field in PROTECTED_FIELDS):
                return {'error': 'Modifica a campi riservati non consentita'}, 403

            doc_ref = self.collection.document(membership_id)
            existing_doc = doc_ref.get()

            if not existing_doc.exists:
                return {'error': 'Membership non trovata'}, 404

            current_data = existing_doc.to_dict()
            updated_data = current_data.copy()
            updated_data.update(data)

            if "card_url" in data:
                return {'error': 'Modifica diretta di card_url non consentita'}, 403

            birthdate = updated_data.get("birthdate")
            if not birthdate or is_minor(birthdate):
                return {'error': 'Utente minorenne non ammesso'}, 403

            email = updated_data.get("email")
            phone = updated_data.get("phone")

            if not email and not phone:
                return {'error': 'Email o telefono obbligatorio'}, 400

            query = self.collection.where("subscription_valid", "==", True)
            potential_duplicates = query.get()

            for doc in potential_duplicates:
                if doc.id == membership_id:
                    continue
                other = doc.to_dict()
                if (email and other.get("email") == email) or (phone and other.get("phone") == phone):
                    return {'error': 'Email o telefono già registrato per un altro membro attivo'}, 409
            print("Updated Data:",updated_data )
            if email and email != current_data.get("email"):
                updated_result = update_membership_card(membership_id, updated_data)
                print("Updated Data:",updated_result )

                if not updated_result.get("success"):
                    return {'error': 'Errore durante la rigenerazione della tessera', 'details': updated_result.get("error")}, 500
                updated_data["card_url"] = updated_result["pdf_url"]
                updated_data["membership_sent"] = False

            doc_ref.update(updated_data)
            return jsonify({'message': 'Membership aggiornata'}), 200

        except Exception as e:
            self.logger.exception("[update]")
            return {'error': str(e)}, 500


    def delete(self, membership_id):
        try:
            doc_ref = self.collection.document(membership_id)
            doc = doc_ref.get()

            if not doc.exists:
                return {'error': 'Membership non trovata'}, 404

            membership_data = doc.to_dict()
            storage_path = membership_data.get("card_storage_path")

            if storage_path:
                blob = self.storage.blob(storage_path)
                if blob.exists():
                    blob.delete()
                    print(f"Tessera rimossa dallo storage: {storage_path}")

            # Rimuove il riferimento alla membershipId nei partecipanti
            participants_query = self.db.collection_group("participants_event") \
                .where("membershipId", "==", membership_id).stream()

            for participant_doc in participants_query:
                participant_ref = participant_doc.reference
                participant_ref.update({"membershipId": firestore.DELETE_FIELD})
                print(f"Rimosso membershipId dal partecipante {participant_ref.id}")

            doc_ref.delete()
            return jsonify({'message': 'Membership eliminata e tessera rimossa'}), 200

        except Exception as e:
            self.logger.error(f"[delete] {e}")
            return {'error': str(e)}, 500

    def send_card(self, membership_id):
        try:
            doc = self.collection.document(membership_id).get()
            if not doc.exists:
                return {'error': 'Membership not found'}, 404

            membership_data = doc.to_dict()
            email = membership_data.get("email")
            name = membership_data.get("name")
            surname = membership_data.get("surname")
            full_name = f"{name}_{surname}"

            card_url = membership_data.get("card_url")
            if not card_url:
                result = process_new_membership(membership_id, membership_data)
                if not result.get("success"):
                    return {'error': 'Card generation failed', 'details': result.get("error")}, 500
                card_url = result["pdf_url"]

            if "memberships/cards/" not in card_url:
                return {'error': 'Invalid card_url format'}, 400

            path_start = card_url.find("memberships/cards/")
            storage_path = card_url[path_start:]

            blob = self.storage.blob(storage_path)
            pdf_data = blob.download_as_bytes()
            pdf_buffer = BytesIO(pdf_data)

            subject = "🎫 La tua tessera MCP"
            html_content = get_membership_email_template(membership_data)
            text_content = f"""
Ciao {name},

Grazie per la tua iscrizione!
In allegato trovi la tua tessera MCP valida fino al {membership_data.get('end_date')}.

Ci vediamo presto,
Il Team MCP
"""

            sent = gmail_send_email_template(
                email,
                subject,
                text_content,
                html_content,
                pdf_buffer,
                f"{full_name}_membership.pdf"
            )

            if sent:
                self.collection.document(membership_id).update({"membership_sent": True})
                return {'message': 'Card sent successfully'}, 200
            else:
                return {'error': 'Failed to send email'}, 500

        except Exception as e:
            self.logger.exception("[send_card]")
            return {'error': str(e)}, 500
    def get_purchases(self, membership_id):
        try:
            doc = self.collection.document(membership_id).get()
            if not doc.exists:
                return {'error': 'Membership non trovata'}, 404

            membership_data = doc.to_dict()
            purchase_ids = membership_data.get("purchases", [])

            if not purchase_ids:
                return jsonify([]), 200

            purchases = []
            for pid in purchase_ids:
                snap = db.collection("purchases").document(pid).get()
                if snap.exists:
                    purchase = snap.to_dict()
                    purchase["id"] = pid
                    purchases.append(purchase)

            return jsonify(purchases), 200

        except Exception as e:
            self.logger.exception("[get_purchases]")
            return {'error': str(e)}, 500
    def get_events(self, membership_id):
        try:
            doc = self.collection.document(membership_id).get()
            if not doc.exists:
                return {'error': 'Membership non trovata'}, 404

            membership_data = doc.to_dict()
            event_ids = membership_data.get("attended_events", [])

            if not event_ids:
                return jsonify([]), 200

            events = []
            for eid in event_ids:
                snap = db.collection("events").document(eid).get()
                if snap.exists:
                    event = snap.to_dict()
                    event["id"] = eid
                    events.append(event)

            return jsonify(events), 200

        except Exception as e:
            self.logger.exception("[get_events]")
            return {'error': str(e)}, 500
    def set_membership_price(self, price):
        try:
            year = str(datetime.now().year)
            self.settings_collection.document("price").set({
                "price_by_year": {year: price}
            }, merge=True)
            return jsonify({"message": f"Prezzo membership per {year} aggiornato a {price}"}), 200
        except Exception as e:
            self.logger.error(f"[set_membership_price] {e}")
            return {"error": str(e)}, 500
    
    def get_membership_price(self):
        try:
            year = str(datetime.now().year)
            doc = self.settings_collection.document("price").get()

            if not doc.exists:
                return {"error": "Prezzo non configurato"}, 404

            price_data = doc.to_dict().get("price_by_year", {})
            price = price_data.get(year)

            if price is None:
                return {"error": f"Nessun prezzo configurato per l'anno {year}"}, 404

            return jsonify({"year": year, "price": price}), 200
        except Exception as e:
            self.logger.error(f"[get_membership_price] {e}")
            return {"error": str(e)}, 500
    
    