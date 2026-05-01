from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from models import Membership
from utils.events_utils import is_minor


def get_minor_validation_error(birthdate: Optional[str]) -> Optional[str]:
    if not birthdate or is_minor(birthdate):
        return "Utente minorenne non ammesso"
    return None


def get_missing_contact_validation_error(email: Optional[str], phone: Optional[str]) -> Optional[str]:
    if not email and not phone:
        return "Email o telefono obbligatorio"
    return None


def resolve_membership_contact_conflict(
    *,
    current_membership_id: Optional[str],
    email_membership: Optional[Membership],
    phone_membership: Optional[Membership],
) -> Optional[Tuple[str, Membership]]:
    if email_membership and email_membership.id != current_membership_id:
        return ("email", email_membership)
    if phone_membership and phone_membership.id != current_membership_id:
        return ("phone", phone_membership)
    return None


def parse_membership_year(start_date: Optional[str], end_date: Optional[str] = None) -> Optional[int]:
    """Ricava l'anno associativo dalle date salvate sul model membership."""
    if start_date:
        try:
            return datetime.fromisoformat(str(start_date).replace("Z", "+00:00")).year
        except Exception:
            pass

    if end_date:
        try:
            parsed = datetime.strptime(str(end_date), "%d-%m-%Y")
            return parsed.year
        except Exception:
            pass
    return None


def build_renewal_record(
    *,
    start_date: str,
    end_date: str,
    purchase_id: Optional[str],
    fee: Optional[float],
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """Crea una voce storica di rinnovo, usata sia dal flusso admin sia dai pagamenti."""
    resolved_year = year or parse_membership_year(start_date, end_date)
    return {
        "year": resolved_year,
        "start_date": start_date,
        "end_date": end_date,
        "purchase_id": purchase_id,
        "fee": fee,
    }


def dedupe_renewals_by_year(renewals: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mantiene una sola voce per anno, fondendo eventuali dati mancanti."""
    deduped: Dict[int, Dict[str, Any]] = {}
    for renewal in renewals:
        if not isinstance(renewal, dict):
            continue
        year_value = renewal.get("year")
        try:
            year = int(year_value)
        except (TypeError, ValueError):
            year = parse_membership_year(
                renewal.get("start_date"),
                renewal.get("end_date"),
            )
        if not year:
            continue

        if year not in deduped:
            deduped[year] = {**renewal, "year": year}
            continue

        current = deduped[year]
        # Se arrivano due record per lo stesso anno, conserviamo il più completo.
        if not current.get("purchase_id") and renewal.get("purchase_id"):
            current["purchase_id"] = renewal.get("purchase_id")
        if current.get("fee") is None and renewal.get("fee") is not None:
            current["fee"] = renewal.get("fee")
        if not current.get("start_date") and renewal.get("start_date"):
            current["start_date"] = renewal.get("start_date")
        if not current.get("end_date") and renewal.get("end_date"):
            current["end_date"] = renewal.get("end_date")

    return [deduped[year] for year in sorted(deduped)]


def membership_years_from_renewals(
    renewals: Iterable[Dict[str, Any]],
    *,
    fallback_start_date: Optional[str] = None,
    fallback_end_date: Optional[str] = None,
) -> List[int]:
    """Deriva l'indice interrogabile degli anni validi a partire dalla cronologia rinnovi."""
    years = {
        int(item["year"])
        for item in dedupe_renewals_by_year(renewals)
        if item.get("year") is not None
    }
    if not years:
        fallback_year = parse_membership_year(fallback_start_date, fallback_end_date)
        if fallback_year:
            years.add(fallback_year)
    return sorted(years)


def is_membership_renewable(membership: Membership, now: Optional[datetime] = None) -> bool:
    """Una membership è rinnovabile solo se non copre già l'anno corrente."""
    now = now or datetime.now(timezone.utc)
    current_year = now.year

    if membership.membership_years and current_year in membership.membership_years:
        return False

    membership_year = parse_membership_year(membership.start_date, membership.end_date)
    if membership_year is None:
        return False
    return membership_year < current_year
