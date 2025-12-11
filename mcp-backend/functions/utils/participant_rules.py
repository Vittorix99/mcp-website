import logging
import unicodedata
from dataclasses import dataclass, field
from itertools import islice
from typing import Dict, List, Set
import requests

from config.external_services import GENDER_API_URL
from config.firebase_config import db
from google.cloud.firestore_v1 import FieldFilter
from utils.events_utils import is_Under_21, is_minor, normalize_email, normalize_phone


logger = logging.getLogger("ParticipantRules")
_GENDER_CACHE: Dict[str, tuple] = {}


@dataclass
class ParticipantCheckResult:
    errors: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    non_members: List[str] = field(default_factory=list)
    membership_docs: Dict[str, Dict] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    s = str(value).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return " ".join(s.split())


def _chunked(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            return
        yield chunk


def _any_already_registered(event_id: str, emails: Set[str], phones: Set[str]) -> bool:
    part_ref = db.collection("participants").document(event_id).collection("participants_event")

    if emails:
        for batch in _chunked(list(emails), 10):
            q = part_ref.where(filter=FieldFilter("email", "in", batch)).limit(1)
            if any(True for _ in q.stream()):
                return True
    if phones:
        for batch in _chunked(list(phones), 10):
            q = part_ref.where(filter=FieldFilter("phone", "in", batch)).limit(1)
            if any(True for _ in q.stream()):
                return True
    return False


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
        _GENDER_CACHE[key] = (gender, round(prob, 2))
        return _GENDER_CACHE[key]
    except Exception as e:
        logger.warning("Gender lookup failed for %s: %s", key, e)
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
                end_dt = datetime.strptime(end_date_s, "%d-%m-%Y").replace(tzinfo=timezone.utc)
                if end_dt >= today:
                    return True
            except Exception:
                pass
        if d.get("active") is True:
            return True
        vu = d.get("valid_until") or d.get("validUntil")
        if vu and isinstance(vu, datetime):
            if vu.tzinfo:
                return vu >= today
            return vu.replace(tzinfo=timezone.utc) >= today
        year = d.get("year") or d.get("membership_year") or d.get("membershipYear")
        if isinstance(year, int) and year == current_year:
            return True
    except Exception as e:
        logger.warning("[participant_rules] is_valid_member parse error: %s", repr(e))
    return False


def run_basic_checks(event_id: str, participants: List[Dict], event_data: Dict) -> ParticipantCheckResult:
    from datetime import datetime, timezone

    result = ParticipantCheckResult()
    today = datetime.now(timezone.utc)

    allow_duplicates = bool(event_data.get("allowDuplicates", False))
    over21_only = bool(event_data.get("over21Only", False))
    only_females = bool(event_data.get("onlyFemales", False))

    seen_emails = set()
    seen_phones = set()
    under21 = []
    non_females = []

    for p in participants:
        name = (p.get("name") or "").strip()
        surname = (p.get("surname") or "").strip()
        email = normalize_email(p.get("email"))
        phone = normalize_phone(p.get("phone"))
        birth = p.get("birthdate")

        if not email or not phone or not birth:
            if "Dati mancanti per alcuni partecipanti: email, telefono o data di nascita." not in result.errors:
                result.errors.append("Dati mancanti per alcuni partecipanti: email, telefono o data di nascita.")
            continue

        if is_minor(birth) and "Uno o più partecipanti non sono maggiorenni." not in result.errors:
            result.errors.append("Uno o più partecipanti non sono maggiorenni.")

        if over21_only:
            try:
                if is_Under_21(birth):
                    under21.append(f"{name} {surname} <{email or phone}>")
            except Exception:
                under21.append(f"{name} {surname} <{email or phone}>")

        if not allow_duplicates and (email in seen_emails or phone in seen_phones):
            msg = "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo."
            if msg not in result.errors:
                result.errors.append(msg)
        seen_emails.add(email)
        seen_phones.add(phone)

        if only_females:
            g, prob = _get_gender_cached(name)
            if g != "female":
                non_females.append(f"{name} {surname} <{email or phone}>")

    if under21:
        result.errors.append(
            "Evento riservato ai maggiori di 21 anni: i seguenti partecipanti non rispettano il requisito: "
            + ", ".join(under21)
        )
    if only_females and non_females:
        result.errors.append("Non è possibile acquistare la partecipazione all'evento al momento")

    if not allow_duplicates and (seen_emails or seen_phones):
        part_ref = db.collection("participants").document(event_id).collection("participants_event")
        if seen_emails:
            q = part_ref.where(filter=FieldFilter("email", "in", list(seen_emails))).limit(1)
            if any(True for _ in q.stream()):
                msg = "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo."
                if msg not in result.errors:
                    result.errors.append(msg)
        if seen_phones:
            q = part_ref.where(filter=FieldFilter("phone", "in", list(seen_phones))).limit(1)
            if any(True for _ in q.stream()):
                msg = "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo."
                if msg not in result.errors:
                    result.errors.append(msg)

    identity_mismatches = []
    for p in participants:
        name = (p.get("name") or "").strip()
        surname = (p.get("surname") or "").strip()
        email = normalize_email(p.get("email"))
        phone = normalize_phone(p.get("phone"))
        label = f"{name} {surname} <{email or phone or 'no-contact'}>".strip()

        has_contact = bool(email or phone)
        if not has_contact:
            result.non_members.append(f"{name} {surname} <contatti mancanti>")
            continue

        is_member = False
        chosen_doc = None
        if email:
            matches = list(db.collection("memberships").where("email", "==", email).stream())
            for mdoc in matches:
                if _is_valid_member(mdoc, today):
                    chosen_doc = mdoc
                    break
            if chosen_doc:
                md = chosen_doc.to_dict() or {}
                m_name_norm = _normalize_text(md.get("name"))
                m_surname_norm = _normalize_text(md.get("surname"))
                provided_n = _normalize_text(name)
                provided_s = _normalize_text(surname)
                if (m_name_norm and m_surname_norm) and (m_name_norm != provided_n or m_surname_norm != provided_s):
                    identity_mismatches.append(f"{name} {surname} <{email}>")
                else:
                    is_member = True
                    label = f"{md.get('name','').strip()} {md.get('surname','').strip()} <{email}>".strip()
        if is_member:
            result.members.append(label)
            if email and chosen_doc:
                result.membership_docs[email] = {"id": chosen_doc.id, "data": chosen_doc.to_dict() or {}}
        else:
            result.non_members.append(label)

    if identity_mismatches:
        result.errors.append(
            "Alcuni partecipanti risultano già tesserati con la stessa email ma nome/cognome non coincidono: "
            + ", ".join(identity_mismatches)
        )

    return result
