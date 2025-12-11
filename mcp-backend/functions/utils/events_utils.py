import datetime
import logging
import re
from datetime import datetime as dt
from typing import Any, Dict, Optional, Union

from models import Event, EventPurchaseAccessType

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def is_minor(birthdate_str):
    """Restituisce True se la persona è minorenne. Accetta formato 'gg-mm-aaaa'."""
    try:
        birthdate = datetime.datetime.strptime(birthdate_str, "%d-%m-%Y").date()
        print("Birthday is:", birthdate)
        today = datetime.date.today()
        return (today - birthdate).days // 365 < 18
    except Exception:
        return True  # In caso di parsing fallito, consideriamo minorenne per sicurezza


def is_Under_21(birthdate_str):
    """Restituisce True se la persona è minorenne. Accetta formato 'gg-mm-aaaa'."""
    try:
        birthdate = datetime.datetime.strptime(birthdate_str, "%d-%m-%Y").date()
        print("Birthday is:", birthdate)
        today = datetime.date.today()
        return (today - birthdate).days // 365 < 21
    except Exception:
        return True  # In caso di parsing fallito, consideriamo minorenne per sicurezza


def calculate_end_of_year(date_input):
    """
    Riceve una data come stringa ISO o datetime.
    Restituisce la fine dell'anno nel formato "gg-mm-aaaa" oppure None se errore.
    """
    try:
        if isinstance(date_input, datetime):
            dt = date_input
        elif isinstance(date_input, str):
            dt = datetime.fromisoformat(date_input.replace("Z", ""))
        else:
            raise ValueError("Unsupported date input type")

        return f"31-12-{dt.year}"
    except Exception:
        logging.exception("Failed to calculate end of year")
        return None


def calculate_end_of_year_membership(date_input):
    """
    Calcola la fine dell’anno dato un datetime o stringa ISO. Output: '31-12-YYYY'.
    """
    try:
        if isinstance(date_input, str):
            date_input = dt.fromisoformat(date_input.replace("Z", ""))
        elif not isinstance(date_input, dt):
            raise TypeError("Expected a datetime or ISO string.")

        return f"31-12-{date_input.year}"
    except Exception as e:
        import logging
        logging.exception("Failed to calculate end of year")
        return None
    except Exception as e:
        import logging
        logging.exception("Failed to calculate end of year")
        return None


def sanitize_event(event: dict) -> dict:
    """Rimuove i campi admin-only da un dizionario evento"""
    hidden_fields = ['participantsCount', 'maxParticipants', 'createdBy', 'updatedBy', 'location']
    return {k: v for k, v in event.items() if k not in hidden_fields}


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip().lower()))


def ensure_event_is_active(event_data: Union[Event, Dict[str, Any]]):
    """
    Ensure an event (model or raw dict) is active and scheduled in the future.
    """
    if isinstance(event_data, Event):
        active = bool(event_data.active)
        date_str = event_data.date
    else:
        if not event_data:
            raise ValueError("Invalid or inactive event")
        active = bool(event_data.get("active", False))
        date_str = event_data.get("date")

    if not active:
        raise ValueError("Invalid or inactive event")

    if not date_str:
        return

    try:
        event_date = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError("Invalid event date format") from exc

    if event_date < datetime.date.today():
        raise ValueError("Event date has already passed")


_LEGACY_PURCHASE_MODE_MAP = {
    "onlymembers": EventPurchaseAccessType.ONLY_MEMBERS,
    "only_members": EventPurchaseAccessType.ONLY_MEMBERS,
    "community": EventPurchaseAccessType.ONLY_MEMBERS,
    "custom_ep13": EventPurchaseAccessType.ONLY_MEMBERS,
    "onlyalreadyregisteredmembers": EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS,
    "only_already_registered_members": EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS,
    "custom_ep12": EventPurchaseAccessType.PUBLIC,
    "standard": EventPurchaseAccessType.PUBLIC,
    "free": EventPurchaseAccessType.PUBLIC,
    "external": EventPurchaseAccessType.PUBLIC,
    "external_link": EventPurchaseAccessType.PUBLIC,
    "private": EventPurchaseAccessType.ON_REQUEST,
    "onrequest": EventPurchaseAccessType.ON_REQUEST,
    "on_request": EventPurchaseAccessType.ON_REQUEST,
}


def map_purchase_mode(value: Optional[str]) -> EventPurchaseAccessType:
    if not value:
        return EventPurchaseAccessType.PUBLIC

    normalized = str(value).strip()
    lowered = normalized.lower()
    if lowered in _LEGACY_PURCHASE_MODE_MAP:
        return _LEGACY_PURCHASE_MODE_MAP[lowered]

    cleaned = normalized.replace("-", "_").replace(" ", "_").upper()
    for candidate in (cleaned, normalized.upper()):
        try:
            return EventPurchaseAccessType(candidate)
        except ValueError:
            continue
    return EventPurchaseAccessType.PUBLIC


def build_event_from_data(data: Optional[Dict[str, Any]], doc_id: Optional[str] = None) -> Event:
    payload = data or {}
    event = Event.from_firestore(payload, doc_id)
    raw_type = payload.get("type") or event.purchase_mode.value
    event.purchase_mode = map_purchase_mode(raw_type)
    return event


def normalize_email(value: str) -> str:
    """Normalizza un indirizzo email rimuovendo spazi e forzando il lowercase."""
    if not value:
        return ""
    return str(value).strip().lower().replace(" ", "")


def normalize_phone(value: str) -> str:
    """Normalizza un numero di telefono eliminando spazi e prefissi non numerici."""
    if not value:
        return ""
    s = str(value).strip().replace(" ", "")
    return re.sub(r"^[A-Za-z]+", "", s)
