# services/admin/memberships_service.py

import logging
from datetime import datetime, timezone
from io import BytesIO

from firebase_admin import firestore
from flask import jsonify
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import bucket, db
from models import Membership
from services.mail_service import gmail_send_email_template
from utils.email_templates import get_membership_email_template
from utils.events_utils import calculate_end_of_year_membership, is_minor, normalize_email, normalize_phone
from utils.membership_cards import process_new_membership, update_membership_card
from utils.slug_utils import build_slug


PROTECTED_FIELDS = ["card_storage_path", "purchase_id"]


class MembershipsService:
    def __init__(self):
        self.db = db
        self.collection = self.db.collection("memberships")
        self.logger = logging.getLogger("MembershipsService")
        self.storage = bucket
        self.settings_collection = self.db.collection("membership_settings")

    def _membership_from_snapshot(self, snapshot) -> Membership:
        return Membership.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def _serialize_membership(self, membership: Membership):
        data = membership.to_firestore(include_none=True)
        data["id"] = membership.id
        return data

    def _parse_iso_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=None)
        except ValueError:
            return None

    def _normalize_name(self, value):
        return (value or "").strip().lower()

    def _format_timestamp(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _parse_amount(self, value):
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _safe_divide_amount(self, amount, count):
        if amount is None or not count:
            return None
        return amount / count

    def _membership_from_id(self, membership_id):
        if not membership_id:
            return None
        snap = self.collection.document(membership_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        data["id"] = membership_id
        return data

    def _chunked(self, items, size=10):
        if not items:
            return
        for i in range(0, len(items), size):
            yield items[i:i + size]

    def get_all(self):
        try:
            docs = self.collection.stream()
            memberships = [self._serialize_membership(self._membership_from_snapshot(doc)) for doc in docs]
            return jsonify(memberships), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {'error': str(e)}, 500

    def get_by_id(self, membership_id, slug: str = None):
        try:
            doc = None
            if slug:
                matches = self.collection.where("slug", "==", slug).limit(1).get()
                if matches:
                    doc = matches[0]
            if doc is None and membership_id:
                doc = self.collection.document(membership_id).get()
            if not doc or not doc.exists:
                return {'error': 'Membership not found'}, 404
            membership = self._membership_from_snapshot(doc)
            return jsonify(self._serialize_membership(membership)), 200
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

            email = normalize_email(data.get("email"))
            phone = normalize_phone(data.get("phone"))
            if not email and not phone:
                return {'error': 'Email o telefono obbligatorio'}, 400

            if email:
                existing = self.collection.where("email", "==", email).limit(1).get()
                if existing:
                    return {'error': 'Email già registrata'}, 409
            if phone:
                existing = self.collection.where("phone", "==", phone).limit(1).get()
                if existing:
                    return {'error': 'Telefono già registrato'}, 409

            now = datetime.now(timezone.utc)
            start_date = now.isoformat()
            end_date = calculate_end_of_year_membership(now)

            send_card_on_create = data.get("send_card_on_create") is True

            membership = Membership(
                name=data.get("name", ""),
                surname=data.get("surname", ""),
                email=email,
                phone=phone,
                birthdate=birthdate,
                start_date=start_date,
                end_date=end_date,
                subscription_valid=True,
                membership_sent=False,
                membership_type=data.get("membership_type", "manual"),
                purchase_id=None,
                send_card_on_create=send_card_on_create,
            )

            doc_ref = self.collection.document()
            membership_id = doc_ref.id
            membership.slug = build_slug(membership.name, membership.surname, suffix=membership_id[-6:])
            doc_ref.set(membership.to_firestore(include_none=True))
            self.logger.info(f"[create] Membership created with ID: {membership_id}")
            return jsonify({'message': 'Membership created', 'id': membership_id}), 201

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

            current_data = existing_doc.to_dict() or {}
            updated_data = current_data.copy()
            updated_data.update(data)

            if "card_url" in data:
                return {'error': 'Modifica diretta di card_url non consentita'}, 403

            birthdate = updated_data.get("birthdate")
            if not birthdate or is_minor(birthdate):
                return {'error': 'Utente minorenne non ammesso'}, 403

            email = normalize_email(updated_data.get("email"))
            phone = normalize_phone(updated_data.get("phone"))
            updated_data["email"] = email or None
            updated_data["phone"] = phone or None

            if not email and not phone:
                return {'error': 'Email o telefono obbligatorio'}, 400

            if email:
                potential_duplicates = self.collection.where("email", "==", email).get()
                for doc in potential_duplicates:
                    if doc.id != membership_id:
                        return {'error': 'Email già registrata per un altro membro'}, 409
            if phone:
                potential_duplicates = self.collection.where("phone", "==", phone).get()
                for doc in potential_duplicates:
                    if doc.id != membership_id:
                        return {'error': 'Telefono già registrato per un altro membro'}, 409
            print("Updated Data:",updated_data )
            if email and email != current_data.get("email"):
                updated_result = update_membership_card(membership_id, updated_data)
                print("Updated Data:",updated_result )

                if not updated_result.get("success"):
                    return {'error': 'Errore durante la rigenerazione della tessera', 'details': updated_result.get("error")}, 500
                updated_data["card_url"] = updated_result["pdf_url"]
                updated_data["membership_sent"] = False

            membership_payload = Membership.from_firestore(updated_data, membership_id).to_firestore(include_none=True)
            doc_ref.set(membership_payload)
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
                    purchase = snap.to_dict() or {}
                    purchases.append({
                        "id": pid,
                        "type": purchase.get("type"),
                        "amount_total": purchase.get("amount_total"),
                        "currency": purchase.get("currency"),
                        "timestamp": purchase.get("timestamp"),
                        "ref_id": purchase.get("ref_id"),
                        "transaction_id": purchase.get("transaction_id"),
                    })

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
                    event = snap.to_dict() or {}
                    events.append({
                        "id": eid,
                        "title": event.get("title"),
                        "date": event.get("date"),
                        "image": event.get("image"),
                    })

            return jsonify(events), 200

        except Exception as e:
            self.logger.exception("[get_events]")
            return {'error': str(e)}, 500
    def set_membership_price(self, price, year=None):
        try:
            year = str(year or datetime.now().year)
            self.settings_collection.document("price").set({
                "price_by_year": {year: price}
            }, merge=True)
            return jsonify({"message": f"Prezzo membership per {year} aggiornato a {price}"}), 200
        except Exception as e:
            self.logger.error(f"[set_membership_price] {e}")
            return {"error": str(e)}, 500
    
    def get_membership_price(self, year=None):
        try:
            year = str(year or datetime.now().year)
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

    def get_memberships_report(self, event_id):
        try:
            if not event_id:
                return {"error": "Missing event_id"}, 400

            event_snap = db.collection("events").document(event_id).get()
            if not event_snap.exists:
                return {"error": "Evento non trovato"}, 404

            event_data = event_snap.to_dict() or {}
            # Membership fee used to compute quota variabile for new associates.
            membership_fee = None
            price_doc = self.settings_collection.document("price").get()
            if price_doc.exists:
                year = str(datetime.now().year)
                price_data = price_doc.to_dict().get("price_by_year", {})
                membership_fee = self._parse_amount(price_data.get(year))

            # Load all purchases for the event.
            purchase_snaps = (
                db.collection("purchases")
                .where(filter=FieldFilter("ref_id", "==", event_id))
                .stream()
            )
            purchases = {}
            total_net_collected = 0.0
            for snap in purchase_snaps:
                purchase_data = snap.to_dict() or {}
                purchases[snap.id] = purchase_data
                net_amount = self._parse_amount(purchase_data.get("net_amount")) or 0.0
                total_net_collected += net_amount
            print(f"[get_memberships_report] event_id={event_id} purchases={len(purchases)}")

            memberships_by_purchase = {}
            membership_cache = {}
            new_member_ids = set()

            # Resolve new associates: memberships created by each purchase.
            purchase_ids = list(purchases.keys())
            for batch in self._chunked(purchase_ids, 10):
                membership_snaps = (
                    self.collection
                    .where(filter=FieldFilter("purchase_id", "in", batch))
                    .stream()
                )
                for m_snap in membership_snaps:
                    m_data = m_snap.to_dict() or {}
                    m_data["id"] = m_snap.id
                    purchase_id = m_data.get("purchase_id")
                    if purchase_id:
                        memberships_by_purchase.setdefault(purchase_id, []).append(m_data)
                    membership_cache[m_snap.id] = m_data
                    new_member_ids.add(m_snap.id)

            rows = []

            # Load participants for the event to include already-associated members.
            participants_snaps = (
                db.collection("participants")
                .document(event_id)
                .collection("participants_event")
                .stream()
            )

            participants_by_purchase = {}
            participant_membership_ids = set()
            for snap in participants_snaps:
                data = snap.to_dict() or {}
                membership_id = data.get("membershipId") or data.get("membership_id")
                purchase_id = data.get("purchase_id")
                if not membership_id or not purchase_id:
                    continue
                participants_by_purchase.setdefault(purchase_id, []).append(membership_id)
                participant_membership_ids.add(membership_id)
            print(
                f"[get_memberships_report] participants={len(participant_membership_ids)} "
                f"participants_purchases={len(participants_by_purchase)}"
            )

            missing_member_ids = [
                mid for mid in participant_membership_ids if mid not in membership_cache
            ]
            for batch in self._chunked(missing_member_ids, 10):
                doc_refs = [self.collection.document(member_id) for member_id in batch]
                member_snaps = (
                    self.collection
                    .where(filter=FieldFilter("__name__", "in", doc_refs))
                    .stream()
                )
                for m_snap in member_snaps:
                    m_data = m_snap.to_dict() or {}
                    m_data["id"] = m_snap.id
                    membership_cache[m_snap.id] = m_data

            # Build rows for new associates (Associato = Si).
            for purchase_id, members in memberships_by_purchase.items():
                purchase = purchases.get(purchase_id, {})
                net_amount = self._parse_amount(purchase.get("net_amount"))
                participants = participants_by_purchase.get(purchase_id)
                total_participants = len(participants) if participants else len(members)
                net_per_member = self._safe_divide_amount(net_amount, total_participants)

                for member in members:
                    quota_variabile = net_per_member
                    if net_per_member is not None and membership_fee is not None:
                        quota_variabile = net_per_member - membership_fee

                    rows.append({
                        "data_iscrizione": member.get("start_date"),
                        "name": member.get("name", ""),
                        "surname": member.get("surname", ""),
                        "email": member.get("email", ""),
                        "associato": "Si",
                        "netto_pagato": net_per_member,
                        "quota_variabile": quota_variabile,
                    })

            # Build rows for existing associates (Associato = No).
            existing_associates_count = 0
            for purchase_id, membership_ids in participants_by_purchase.items():
                purchase = purchases.get(purchase_id, {})
                net_amount = self._parse_amount(purchase.get("net_amount"))
                net_per_participant = self._safe_divide_amount(net_amount, len(membership_ids))

                for membership_id in membership_ids:
                    if membership_id in new_member_ids:
                        continue
                    member = membership_cache.get(membership_id)
                    if not member:
                        continue

                    rows.append({
                        "data_iscrizione": member.get("start_date"),
                        "name": member.get("name", ""),
                        "surname": member.get("surname", ""),
                        "email": member.get("email", ""),
                        "associato": "No",
                        "netto_pagato": net_per_participant,
                        "quota_variabile": net_per_participant,
                    })
                    existing_associates_count += 1

            # Sort by membership start date.
            rows.sort(
                key=lambda r: self._parse_iso_date(r.get("data_iscrizione")) or datetime.max
            )

            response = {
                "event_id": event_id,
                "new_associates_count": len(new_member_ids),
                "existing_associates_count": existing_associates_count,
                "total_net_collected": total_net_collected,
                "rows": rows,
            }
            print(
                f"[get_memberships_report] rows={len(rows)} new_associates={len(new_member_ids)}"
            )
            return jsonify(response), 200
        except Exception as e:
            self.logger.exception("[get_memberships_report]")
            return {"error": str(e)}, 500
    
    
