
# --- Helper: strict EP12 duplicate check (already registered in DB) ---
from itertools import islice


import logging
from config.firebase_config import db
from utils.events_utils import is_minor, calculate_end_of_year, is_Under_21
from flask import jsonify
from google.cloud.firestore_v1 import FieldFilter
import os
import unicodedata
import requests
from config.event_types import EventTypes

GENDER_API_URL = os.environ.get("GENDER_API_URL", "https://api.genderize.io")
# --- Gender helper with simple cache ---
_GENDER_CACHE = {}



def _normalize_email(email: str) -> str:
    if not email:
        return ""
    return str(email).strip().lower().replace(" ", "")


def _normalize_phone(value: str) -> str:
        if not value:
            return ""
        import re
        s = str(value).strip().replace(" ", "")
        # Remove any leading alphabetic (non-numeric, non-+) characters from the start (e.g. 'IT', 'it', 'abc')
        s = re.sub(r"^[A-Za-z]+", "", s)
        return s



def _chunked(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            return
        yield chunk


def _any_already_registered(event_id: str, emails: set, phones: set) -> bool:
    """Return True if any of the provided emails/phones is already present in participants_event for the event.
    Uses chunked 'in' queries (max 10 per Firestore limitation).
    """
    part_ref = db.collection("participants").document(event_id).collection("participants_event")

    # Check emails
    if emails:
        for batch in _chunked(list(emails), 10):
            q = part_ref.where(filter=FieldFilter("email", "in", batch)).limit(1)
            if any(True for _ in q.stream()):
                return True
    # Check phones
    if phones:
        for batch in _chunked(list(phones), 10):
            q = part_ref.where(filter=FieldFilter("phone", "in", batch)).limit(1)
            if any(True for _ in q.stream()):
                return True
    return False



def _normalize_text(value: str) -> str:
    """Lowercase, strip, remove diacritics, collapse spaces. Safe for None."""
    if not value:
        return ""
    s = str(value).strip().lower()
    # remove diacritics
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    # collapse multiple spaces
    s = " ".join(s.split())
    return s






def _get_gender_cached(name: str):
    key = (name or "").strip().split(" ")[0].lower()
    if not key:
        return ("N/A", 0.0)
    if key in _GENDER_CACHE:
        return _GENDER_CACHE[key]
    try:
        resp = requests.get(GENDER_API_URL, params={"name": key}, timeout=5)
        resp.raise_for_status()
        data = resp.json() or {}
        gender = data.get("gender") or "N/A"
        prob = float(data.get("probability", 0.0) or 0.0)
        prob = round(prob, 2)
        print("[DEBUG][GENDER]", key, "→", gender, prob, data)
        _GENDER_CACHE[key] = (gender, prob)
        return _GENDER_CACHE[key]
    except Exception as e:
        print(f"[ERROR][GENDER] lookup failed for '{key}': {str(e)}")
        _GENDER_CACHE[key] = ("N/A", 0.0)
        return _GENDER_CACHE[key]


def _is_valid_member(doc, today=None):
    from datetime import datetime, timezone
    if today is None:
        today = datetime.now(timezone.utc)
    current_year = today.year
    try:
        d = doc.to_dict() or {}
        if d.get("subscription_valid") is True:
            return True
        end_date_s = d.get("end_date")
        if end_date_s:
            try:
                from datetime import datetime as _dt
                end_dt = _dt.strptime(end_date_s, "%d-%m-%Y").replace(tzinfo=timezone.utc)
                if end_dt >= today:
                    return True
            except Exception:
                pass
        if d.get("active") is True:
            return True
        vu = d.get("valid_until") or d.get("validUntil")
        if vu:
            def _to_dt(value):
                from datetime import datetime as _dt, timezone as _tz
                if isinstance(value, _dt):
                    return value if value.tzinfo else value.replace(tzinfo=_tz.utc)
                try:
                    if hasattr(value, "seconds"):
                        return _dt.fromtimestamp(value.seconds + getattr(value, "nanos", 0) / 1e9, tz=_tz.utc)
                except Exception:
                    pass
                if isinstance(value, str):
                    for fmt in ("%Y-%m-%d","%d-%m-%Y","%Y-%m-%dT%H:%M:%S%z","%Y-%m-%dT%H:%M:%S.%f%z","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M:%S.%f"):
                        try:
                            dt = _dt.strptime(value, fmt)
                            return dt if dt.tzinfo else dt.replace(tzinfo=_tz.utc)
                        except Exception:
                            continue
                return None
            vu_dt = _to_dt(vu)
            if vu_dt and vu_dt >= today:
                return True
        year = d.get("year") or d.get("membership_year") or d.get("membershipYear")
        if isinstance(year, int) and year == current_year:
            return True
    except Exception as e:
        print(f"[CHK][COMMON] is_valid_member parse error: {repr(e)}")
    return False


def common_checks(event_id: str, participants: list, event_data: dict):
    """
    Esegue i controlli comuni a TUTTI gli eventi:
    - campi mancanti, minorenni
    - over21Only
    - onlyFemales (via genderize)
    - duplicati nel carrello + già registrati, se allowDuplicates = False
    - membership lookup + identità stretta (email primaria): ritorna members/non_members
    Ritorna: (errors: list[str], members: list[str], non_members: list[str])
    """
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc)

    allow_duplicates = bool(event_data.get("allowDuplicates", False))
    over21_only = bool(event_data.get("over21Only", False))
    only_females = bool(event_data.get("onlyFemales", False))

    errors = []
    seen_emails = set()
    seen_phones = set()

    under21 = []
    non_females = []

    # Pass 1: validazioni locali e raccolta duplicati in cart
    for p in participants:
        name = (p.get("name") or "").strip()
        surname = (p.get("surname") or "").strip()
        email = _normalize_email(p.get("email"))
        phone = _normalize_phone(p.get("phone"))
        birth = p.get("birthdate")

        if not email or not phone or not birth:
            if "Dati mancanti per alcuni partecipanti: email, telefono o data di nascita." not in errors:
                errors.append("Dati mancanti per alcuni partecipanti: email, telefono o data di nascita.")
            continue

        if is_minor(birth):
            if "Uno o più partecipanti non sono maggiorenni." not in errors:
                errors.append("Uno o più partecipanti non sono maggiorenni.")

        if over21_only:
            try:
                if is_Under_21(birth):  # fail-safe: True anche se parsing fallisce
                    under21.append(f"{name} {surname} <{email or phone}>")
            except Exception:
                # In caso di eccezioni inattese, trattiamo come under 21 per sicurezza
                under21.append(f"{name} {surname} <{email or phone}>")

        if not allow_duplicates and (email in seen_emails or phone in seen_phones):
            if "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo." not in errors:
                errors.append("Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo.")
        seen_emails.add(email)
        seen_phones.add(phone)

        if only_females:
            g, prob = _get_gender_cached(name)
            if g != "female":
                non_females.append(f"{name} {surname} <{email or phone}>")

    if under21:
        errors.append("Evento riservato ai maggiori di 21 anni: i seguenti partecipanti non rispettano il requisito: " + ", ".join(under21))
    if only_females and non_females:
        errors.append("Non è possibile acquistare la partecipazione all'evento al momento")

    # Pass 2: duplicati già registrati (DB)
    if not allow_duplicates and (seen_emails or seen_phones):
        part_ref = db.collection("participants").document(event_id).collection("participants_event")
        if seen_emails:
            q = part_ref.where(filter=FieldFilter("email", "in", list(seen_emails))).limit(1)
            email_matches = sum(1 for _ in q.stream())
            if email_matches > 0 and "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo." not in errors:
                errors.append("Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo.")
        if seen_phones:
            q = part_ref.where(filter=FieldFilter("phone", "in", list(seen_phones))).limit(1)
            phone_matches = sum(1 for _ in q.stream())
            if phone_matches > 0 and "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo." not in errors:
                errors.append("Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo.")

    # Pass 3: membership lookup + identità stretta ⇒ build members/non_members and identity errors
    members = []
    non_members = []
    identity_mismatches = []

    for p in participants:
        name = (p.get("name") or "").strip()
        surname = (p.get("surname") or "").strip()
        email = _normalize_email(p.get("email"))
        phone = _normalize_phone(p.get("phone"))
        label = f"{name} {surname} <{email or phone or 'no-contact'}>".strip()

        has_contact = bool(email or phone)
        if not has_contact:
            non_members.append(f"{name} {surname} <contatti mancanti>")
            continue

        is_member = False
        if email:
            matches = list(db.collection("memberships").where("email", "==", email).stream())
            chosen = None
            for mdoc in matches:
                if _is_valid_member(mdoc, today):
                    chosen = mdoc
                    break
            if chosen:
                md = chosen.to_dict() or {}
                m_name_norm = _normalize_text(md.get("name"))
                m_surname_norm = _normalize_text(md.get("surname"))
                provided_n = _normalize_text(name)
                provided_s = _normalize_text(surname)
                if (m_name_norm and m_surname_norm) and (m_name_norm != provided_n or m_surname_norm != provided_s):
                    identity_mismatches.append(f"{name} {surname} <{email}>")
                else:
                    is_member = True
                    label = f"{md.get('name','').strip()} {md.get('surname','').strip()} <{email}>".strip()
        if not is_member and phone:
            by_phone = db.collection("memberships").where("phone", "==", phone).stream()
            is_member = any(_is_valid_member(doc, today) for doc in by_phone)

        if is_member:
            members.append(label)
        else:
            non_members.append(label)

    if identity_mismatches:
        errors.append("Alcuni partecipanti risultano già tesserati con la stessa email ma nome/cognome non coincidono: " + ", ".join(identity_mismatches))

    return errors, members, non_members

# --- EP12: logica classica (missing fields, minor, duplicati, già registrati) ---
def check_participants_ep12(event_id, participants, allow_duplicates=False):
    print(f"[CHK][EP12] start: event_id={event_id} participants={len(participants)}")
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

        if not allow_duplicates and (email in seen_emails or phone in seen_phones):
            raw_errors.append("duplicate_cart")

        seen_emails.add(email)
        seen_phones.add(phone)

    print(f"[CHK][EP12] collected emails={len(seen_emails)} phones={len(seen_phones)} raw_errors_pre_query={raw_errors}")

    already_reg = False
    if not allow_duplicates:
        part_ref = db.collection("participants").document(event_id).collection("participants_event")

        if seen_emails:
            q = part_ref.where(filter=FieldFilter("email", "in", list(seen_emails))).limit(1)
            email_matches = sum(1 for _ in q.stream())
            print(f"[CHK][EP12] email matches in DB: {email_matches}")
            if email_matches > 0:
                already_reg = True

        if not already_reg and seen_phones:
            q = part_ref.where(filter=FieldFilter("phone", "in", list(seen_phones))).limit(1)
            phone_matches = sum(1 for _ in q.stream())
            print(f"[CHK][EP12] phone matches in DB: {phone_matches}")
            if phone_matches > 0:
                already_reg = True

        if already_reg:
            raw_errors.append("already_registered")
            print("[CHK][EP12] already_registered appended (once)")
    else:
        print("[CHK][EP12] allow_duplicates=True → skip DB duplicate checks")

    print(f"[CHK][EP12] raw_errors_post_query={raw_errors}")

    errors = set()
    if ("already_registered" in raw_errors) or (not allow_duplicates and "duplicate_cart" in raw_errors):
        errors.add("Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo.")

    if "minor" in raw_errors:
        errors.add("Uno o più partecipanti non sono maggiorenni.")

    if "missing_fields" in raw_errors:
        errors.add("Dati mancanti per alcuni partecipanti: email, telefono o data di nascita.")

    if errors:
        print(f"[CHK][EP12] result: VALID=False errors={list(errors)}")
        return jsonify({"valid": False, "errors": list(errors)}), 400

    print("[CHK][EP12] result: VALID=True")
    return jsonify({"valid": True}), 200


def check_participants_service(data):
    event_id = data.get("eventId")
    participants = data.get("participants", [])
    print(f"[CHK][SRV] payload keys={list(data.keys())}")
    print(f"[CHK][SRV] eventId={event_id} participants={len(participants)}")

    if not event_id or not isinstance(participants, list) or not participants:
        return jsonify({"error": "eventId o participants mancanti"}), 400

    # Carica evento e parametri
    event_doc = db.collection("events").document(event_id).get()
    if not event_doc.exists:
        return jsonify({"error": "Evento non trovato"}), 404
    event_data = event_doc.to_dict() or {}

    raw_event_type = (event_data.get("type") or "").lower()
    try:
        event_type = EventTypes(raw_event_type)
    except Exception:
        event_type = None
    print(f"[CHK][SRV] event_type_raw={raw_event_type} enum={event_type}")

    # 1) Esegui sempre i controlli comuni
    errors, members, non_members = common_checks(event_id, participants, event_data)
    if errors:
        print(f"[CHK][SRV] common errors → 400: {errors}")
        return jsonify({"valid": False, "errors": errors}), 400

    # 1.5) Enforce onlyMembers globally for ANY event
    only_members = bool(event_data.get("onlyMembers", False))
    if only_members and non_members:
        msg = "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: " + ", ".join(non_members)
        print(f"[CHK][SRV] onlyMembers (global) violation → 400: {non_members}")
        return jsonify({"valid": False, "errors": [msg]}), 400

    # 2) Regole addizionali per tipo evento
    if event_type == EventTypes.CUSTOM_EP13:
        # Se onlyMembers è true, sarebbe già stato bloccato dal check globale qui sopra.
        # EP13 con onlyMembers=False → non blocchiamo, annotiamo.
        print(f"[CHK][SRV][EP13] VALID=True annotate members={len(members)} nonMembers={len(non_members)}")
        return jsonify({"valid": True, "members": members, "nonMembers": non_members}), 200

    if event_type == EventTypes.CUSTOM_EP12:
        # EP12: blocca SEMPRE chi è già registrato all'evento (partecipation already purchased),
        # indipendentemente da allowDuplicates.
        emails = { _normalize_email(p.get("email")) for p in participants if _normalize_email(p.get("email")) }
        phones = { _normalize_phone(p.get("phone")) for p in participants if _normalize_phone(p.get("phone")) }
        if _any_already_registered(event_id, emails, phones):
            msg = "Uno o più partecipanti hanno già acquistato la partecipazione all'evento."
            print("[CHK][SRV][EP12] already_registered → 400")
            return jsonify({"valid": False, "errors": [msg]}), 400
        print("[CHK][SRV][EP12] VALID=True (no previous registrations)")
        return jsonify({"valid": True}), 200

    # Default: passed common checks
    print("[CHK][SRV] DEFAULT VALID=True")
    return jsonify({"valid": True}), 200