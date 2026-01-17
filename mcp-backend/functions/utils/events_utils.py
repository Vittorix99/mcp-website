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
    Ensure an event (model or raw dict) is active, not sold out, and scheduled in the future.
    """
    if isinstance(event_data, Event):
        status = event_data.status.value if event_data.status else "active"
        date_str = event_data.date
        max_participants = event_data.max_participants
        participants_count = event_data.participants_count
    else:
        if not event_data:
            raise ValueError("Invalid or inactive event")
        status = str(event_data.get("status") or "active")
        date_str = event_data.get("date")
        max_participants = event_data.get("maxParticipants") or event_data.get("max_participants")
        participants_count = event_data.get("participantsCount") or event_data.get("participants_count")

    if status != "active":
        raise ValueError("Invalid or inactive event")

    if max_participants is not None and participants_count is not None:
        try:
            if int(participants_count) >= int(max_participants):
                raise ValueError("Event is sold out")
        except (TypeError, ValueError):
            pass

    if not date_str:
        return

    try:
        event_date = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError("Invalid event date format") from exc

    if event_date < datetime.date.today():
        raise ValueError("Event date has already passed")


def map_purchase_mode(value: Optional[str]) -> EventPurchaseAccessType:
    if not value:
        return EventPurchaseAccessType.PUBLIC

    normalized = str(value).strip()
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
    event.purchase_mode = map_purchase_mode(event.purchase_mode.value if event.purchase_mode else None)
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
