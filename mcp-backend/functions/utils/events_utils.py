import datetime
import logging
import re
from datetime import datetime as dt
from typing import Any, Dict, Optional, Union

from models import Event, EventPurchaseAccessType

# RFC-5322 semplificata (pragmatica): valida local-part comune e dominio con almeno un dot.
EMAIL_REGEX = re.compile(
    r"^(?!\.)[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+(?<!\.)@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


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
        if isinstance(date_input, dt):
            resolved = date_input
        elif isinstance(date_input, str):
            resolved = dt.fromisoformat(date_input.replace("Z", ""))
        else:
            raise ValueError("Unsupported date input type")

        return f"31-12-{resolved.year}"
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


def to_iso8601_datetime(value: Optional[str]) -> Optional[str]:
    """
    Normalizza una data in ISO 8601 completo con timezone.
    Accetta:
    - ISO 8601 (es: 2026-12-31T23:59:59Z)
    - formato legacy gg-mm-aaaa (es: 31-12-2026)
    - formato yyyy-mm-dd
    """
    if value is None:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    try:
        parsed = dt.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.isoformat(timespec="seconds")
    except ValueError:
        pass

    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.datetime.strptime(raw, fmt).replace(
                hour=23,
                minute=59,
                second=59,
                tzinfo=datetime.timezone.utc,
            )
            return parsed.isoformat(timespec="seconds")
        except ValueError:
            continue

    logging.warning("Invalid date time format: %s", raw)
    return None


def sanitize_event(event: dict) -> dict:
    """Rimuove i campi admin-only da un dizionario evento"""
    hidden_fields = ['participantsCount', 'maxParticipants', 'createdBy', 'updatedBy', 'location']
    return {k: v for k, v in event.items() if k not in hidden_fields}


def is_valid_email(email: str) -> bool:
    return validate_email_format(email)


def validate_email_format(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(str(email).strip().lower()))


def ensure_event_is_active(event_data: Union[Event, Dict[str, Any]]):
    """
    Block purchases only when the event is explicitly marked as 'ended'.
    All other statuses (active, sold_out, coming_soon) allow purchases.
    """
    if isinstance(event_data, Event):
        status = event_data.status.value if event_data.status else "active"
    else:
        if not event_data:
            raise ValueError("Invalid or inactive event")
        status = str(event_data.get("status") or "active")

    if status == "ended":
        raise ValueError("Evento terminato: acquisti non consentiti")


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
