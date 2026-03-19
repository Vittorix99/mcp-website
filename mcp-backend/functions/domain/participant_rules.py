import logging
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol, Set, Tuple, Union

import requests

from config.external_services import GENDER_API_URL
from dto import EventDTO, MembershipDTO
from models import Event, Membership
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from utils.events_utils import is_Under_21, is_minor, normalize_email, normalize_phone


logger = logging.getLogger("ParticipantRules")
_GENDER_CACHE: Dict[str, Tuple[str, float]] = {}


class ParticipantLike(Protocol):
    name: str
    surname: str
    email: str
    phone: str
    birthdate: Optional[str]


@dataclass
class ParticipantCheckResult:
    errors: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    non_members: List[str] = field(default_factory=list)
    membership_docs: Dict[str, MembershipDTO] = field(default_factory=dict)

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


def _is_valid_member(member: Membership, today: Optional[datetime] = None) -> bool:
    if today is None:
        today = datetime.now(timezone.utc)
    # A membership from a previous year is always expired, regardless of subscription_valid
    start_date_s = member.start_date
    if start_date_s:
        try:
            start_dt = datetime.fromisoformat(str(start_date_s).replace("Z", "+00:00"))
            if start_dt.year < today.year:
                return False
        except Exception:
            pass
    if member.subscription_valid:
        return True
    end_date_s = member.end_date
    if end_date_s:
        try:
            end_dt = datetime.strptime(end_date_s, "%d-%m-%Y").replace(tzinfo=timezone.utc)
            if end_dt >= today:
                return True
        except Exception:
            return False
    return False


def _resolve_event_flags(event: Union[Event, EventDTO]) -> Tuple[bool, bool, bool]:
    if isinstance(event, Event):
        dto = EventDTO.from_model(event)
    else:
        dto = event
    return (
        bool(dto.allow_duplicates),
        bool(dto.over21_only),
        bool(dto.only_females),
    )


def run_basic_checks(
    event_id: str,
    participants: List[ParticipantLike],
    event_data: Union[Event, EventDTO],
    *,
    participant_repository: Optional[ParticipantRepository] = None,
    membership_repository: Optional[MembershipRepository] = None,
) -> ParticipantCheckResult:
    result = ParticipantCheckResult()
    today = datetime.now(timezone.utc)

    participant_repository = participant_repository or ParticipantRepository()
    membership_repository = membership_repository or MembershipRepository()

    allow_duplicates, over21_only, only_females = _resolve_event_flags(event_data)

    seen_emails: Set[str] = set()
    seen_phones: Set[str] = set()
    under21: List[str] = []
    non_females: List[str] = []

    for participant in participants:
        name = (participant.name or "").strip()
        surname = (participant.surname or "").strip()
        email = normalize_email(participant.email)
        phone = normalize_phone(participant.phone)
        birth = participant.birthdate

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
            gender, _ = _get_gender_cached(name)
            if gender != "female":
                non_females.append(f"{name} {surname} <{email or phone}>")

    if under21:
        result.errors.append(
            "Evento riservato ai maggiori di 21 anni: i seguenti partecipanti non rispettano il requisito: "
            + ", ".join(under21)
        )
    if only_females and non_females:
        result.errors.append("Non è possibile acquistare la partecipazione all'evento al momento")

    if not allow_duplicates and (seen_emails or seen_phones):
        already_registered = participant_repository.any_with_contacts(
            event_id,
            list(seen_emails),
            list(seen_phones),
        )
        if already_registered:
            msg = "Uno o più partecipanti hanno già acquistato la partecipazione all'evento o presentano dati duplicati nel modulo."
            if msg not in result.errors:
                result.errors.append(msg)

    identity_mismatches = []
    for participant in participants:
        name = (participant.name or "").strip()
        surname = (participant.surname or "").strip()
        email = normalize_email(participant.email)
        phone = normalize_phone(participant.phone)
        label = f"{name} {surname} <{email or phone or 'no-contact'}>".strip()

        has_contact = bool(email or phone)
        if not has_contact:
            result.non_members.append(f"{name} {surname} <contatti mancanti>")
            continue

        is_member = False
        member_model: Optional[Membership] = None
        if email:
            member_model = membership_repository.find_model_by_email(email)
            if member_model and _is_valid_member(member_model, today):
                m_name_norm = _normalize_text(member_model.name)
                m_surname_norm = _normalize_text(member_model.surname)
                provided_n = _normalize_text(name)
                provided_s = _normalize_text(surname)
                if (m_name_norm and m_surname_norm) and (m_name_norm != provided_n or m_surname_norm != provided_s):
                    identity_mismatches.append(f"{name} {surname} <{email}>")
                else:
                    is_member = True
                    label = f"{member_model.name.strip()} {member_model.surname.strip()} <{email}>".strip()

        if is_member and member_model:
            result.members.append(label)
            if email:
                result.membership_docs[email] = MembershipDTO.from_model(member_model)
        else:
            result.non_members.append(label)

    if identity_mismatches:
        result.errors.append(
            "Alcuni partecipanti risultano già tesserati con la stessa email ma nome/cognome non coincidono: "
            + ", ".join(identity_mismatches)
        )

    return result
