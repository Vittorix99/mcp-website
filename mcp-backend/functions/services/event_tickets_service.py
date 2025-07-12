import logging
from config.firebase_config import db
from utils.events_utils import is_minor, calculate_end_of_year
from flask import jsonify


import logging
from config.firebase_config import db
from utils.events_utils import is_minor, calculate_end_of_year
from flask import jsonify


def check_participants_service(data):
    event_id = data.get("eventId")
    participants = data.get("participants", [])
    print(data)

    if not event_id or not isinstance(participants, list) or not participants:
        return jsonify({"error": "eventId o participants mancanti"}), 400

    seen_emails = set()
    seen_phones = set()
    raw_errors = []

    for p in participants:
        name = p.get("name", "")
        surname = p.get("surname", "")
        email = (p.get("email") or "").strip().lower()
        phone = (p.get("phone") or "").strip()
        birth = p.get("birthdate")

        if not email or not phone or not birth:
            raw_errors.append("missing_fields")
            continue

        if is_minor(birth):
            raw_errors.append("minor")

        if email in seen_emails or phone in seen_phones:
            raw_errors.append("duplicate_cart")

        seen_emails.add(email)
        seen_phones.add(phone)

    part_ref = db.collection("participants").document(event_id).collection("participants_event")

    if seen_emails:
        q = part_ref.where("email", "in", list(seen_emails))
        for _ in q.stream():
            raw_errors.append("already_registered")

    if seen_phones:
        q = part_ref.where("phone", "in", list(seen_phones))
        for _ in q.stream():
            raw_errors.append("already_registered")

    errors = set()
    if "already_registered" in raw_errors or "duplicate_cart" in raw_errors:
        errors.add("Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo.")

    if "minor" in raw_errors:
        errors.add("Uno o più partecipanti non sono maggiorenni.")

    if "missing_fields" in raw_errors:
        errors.add("Dati mancanti per alcuni partecipanti: email, telefono o data di nascita.")

    if errors:
        return jsonify({"valid": False, "errors": list(errors)}), 400

    return jsonify({"valid": True}), 200