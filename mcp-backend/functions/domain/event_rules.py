from __future__ import annotations

from datetime import date, datetime
from typing import Optional


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
