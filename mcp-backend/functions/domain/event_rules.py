from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo


EVENT_TIMEZONE = ZoneInfo("Europe/Rome")


def normalize_event_date_string(value: str) -> str:
    """
    Accepts ``DD-MM-YYYY``, ``DD/MM/YYYY`` or ``YYYY-MM-DD`` and returns
    the normalized ``DD-MM-YYYY`` representation used by the current domain.
    """
    if not value:
        raise ValueError("Invalid date format. Use DD-MM-YYYY")

    raw = str(value).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    raise ValueError("Invalid date format. Use DD-MM-YYYY")


def parse_event_date(value: Optional[str]) -> Optional[date]:
    """
    Parses stored event dates, accepting both normalized and legacy values.
    """
    if not value:
        return None

    raw = str(value).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_event_time(value: Optional[str]) -> Optional[time]:
    """Parsa orari evento salvati come HH:MM, HH.MM o varianti con AM/PM."""
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    normalized = raw.replace(".", ":").upper()
    for token in ("H", "ORE"):
        normalized = normalized.replace(token, "")
    normalized = " ".join(normalized.split())

    for fmt in ("%H:%M", "%H", "%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(normalized, fmt).time()
        except ValueError:
            continue
    return None


def get_event_start_datetime(event, tzinfo=EVENT_TIMEZONE) -> Optional[datetime]:
    event_date = parse_event_date(getattr(event, "date", None))
    if not event_date:
        return None

    start_time = parse_event_time(getattr(event, "start_time", None)) or time(0, 0)
    return datetime.combine(event_date, start_time, tzinfo=tzinfo)


def get_event_end_datetime(event, tzinfo=EVENT_TIMEZONE) -> Optional[datetime]:
    """Calcola quando l'evento deve considerarsi terminato per bloccare gli acquisti."""
    start_dt = get_event_start_datetime(event, tzinfo=tzinfo)
    if not start_dt:
        return None

    end_time = parse_event_time(getattr(event, "end_time", None))
    if not end_time:
        # "Till late" o valori non parsabili: chiudiamo dopo 12 ore dall'inizio.
        return start_dt + timedelta(hours=12)

    end_dt = datetime.combine(start_dt.date(), end_time, tzinfo=tzinfo)
    if end_dt <= start_dt:
        # Evento notturno: es. 23:00 → 05:00 del giorno dopo.
        end_dt += timedelta(days=1)
    return end_dt


def is_event_finished(event, now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(EVENT_TIMEZONE)
    if now.tzinfo is None:
        now = now.replace(tzinfo=EVENT_TIMEZONE)

    end_dt = get_event_end_datetime(event, tzinfo=now.tzinfo)
    if not end_dt:
        return False
    return now >= end_dt
