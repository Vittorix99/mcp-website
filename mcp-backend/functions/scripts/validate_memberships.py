"""
Validazione coerenza documenti membership.

Controlla che ogni documento rispetti le regole stabilite:

  1. renewals non vuoto
  2. membership_years non vuoto e coerente con renewals
  3. Ogni purchase in purchases[] ha un renewal corrispondente
  4. Ogni renewal con purchase ha il purchase_id corretto (anno del timestamp)
  5. Fee nei renewal coerente con membership_fee (10.0 fallback)
  6. Nessun anno duplicato nei renewals
  7. start_date/end_date top-level coincidono con l'ultimo renewal
  8. purchase_id top-level presente in purchases[] o nei renewals

Uso:
  python scripts/validate_memberships.py               # tutti i membri
  python scripts/validate_memberships.py --limit 50    # subset
  python scripts/validate_memberships.py --verbose      # mostra anche i membri OK
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from itertools import islice
from typing import Any, Dict, List, Optional, Set

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.firebase_config import db
from domain.membership_rules import parse_membership_year


# ---------------------------------------------------------------------------
# Utilities (copiate da migrate_membership_history per autonomia)
# ---------------------------------------------------------------------------

def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _year_from_timestamp(timestamp: Any) -> Optional[int]:
    if timestamp is None:
        return None
    if hasattr(timestamp, "year"):
        return int(timestamp.year)
    if hasattr(timestamp, "to_datetime"):
        return timestamp.to_datetime().year
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.strip().replace("Z", "+00:00")).year
        except ValueError:
            pass
    return None


def _load_purchase_year_map(purchase_ids: List[str]) -> Dict[int, str]:
    """Ritorna {anno: purchase_id} leggendo i documenti purchase."""
    result: Dict[int, str] = {}
    for pid in purchase_ids:
        doc = db.collection("purchases").document(pid).get()
        if not doc.exists:
            continue
        data = doc.to_dict() or {}
        year = _year_from_timestamp(data.get("timestamp"))
        if year is not None and year not in result:
            result[year] = pid
    return result


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _check(membership_id: str, data: Dict[str, Any]) -> List[str]:
    """Ritorna lista di problemi trovati. Lista vuota = tutto OK."""
    issues: List[str] = []

    renewals: List[Dict] = data.get("renewals") or []
    membership_years: List[int] = [_to_int(y) for y in (data.get("membership_years") or []) if _to_int(y) is not None]
    purchases: List[str] = list(data.get("purchases") or [])
    top_purchase_id: Optional[str] = data.get("purchase_id")
    membership_fee = _to_float(data.get("membership_fee"))
    correct_fee = membership_fee if membership_fee is not None else 10.0
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    # Tutti i purchase_ids da considerare (top-level + lista)
    all_purchase_ids = list(purchases)
    if top_purchase_id and top_purchase_id not in all_purchase_ids:
        all_purchase_ids = [top_purchase_id] + all_purchase_ids

    # Legge la mappa anno→purchase_id dai documenti reali
    purchase_year_map = _load_purchase_year_map(all_purchase_ids)

    # --- 1. renewals non vuoto ---
    if not renewals:
        issues.append("renewals vuoto")

    # --- 2. membership_years non vuoto ---
    if not membership_years:
        issues.append("membership_years vuoto")

    # --- 3. anni duplicati nei renewals ---
    renewal_years_list = [_to_int(r.get("year")) for r in renewals if _to_int(r.get("year")) is not None]
    seen: Set[int] = set()
    for y in renewal_years_list:
        if y in seen:
            issues.append(f"anno {y} duplicato nei renewals")
        seen.add(y)
    renewal_years: Set[int] = seen

    # --- 4. membership_years coerente con renewals ---
    years_from_renewals = set(renewal_years)
    years_set = set(membership_years)
    if years_from_renewals != years_set:
        missing_in_years = years_from_renewals - years_set
        extra_in_years = years_set - years_from_renewals
        if missing_in_years:
            issues.append(f"membership_years manca anni presenti nei renewals: {sorted(missing_in_years)}")
        if extra_in_years:
            issues.append(f"membership_years ha anni non presenti nei renewals: {sorted(extra_in_years)}")

    # --- 5. Ogni purchase ha un renewal corrispondente ---
    for year, pid in purchase_year_map.items():
        if year not in renewal_years:
            issues.append(f"purchase {pid} (anno {year}) non ha un renewal corrispondente")

    # --- 6. purchase_id nel renewal corretto ---
    renewal_by_year = {_to_int(r.get("year")): r for r in renewals if _to_int(r.get("year")) is not None}
    for year, expected_pid in purchase_year_map.items():
        renewal = renewal_by_year.get(year)
        if renewal is None:
            continue  # già segnalato sopra
        actual_pid = renewal.get("purchase_id")
        if actual_pid != expected_pid:
            issues.append(
                f"renewal {year}: purchase_id errato "
                f"(atteso={expected_pid}, trovato={actual_pid})"
            )

    # --- 7. fee nei renewal coerente ---
    for r in renewals:
        year = _to_int(r.get("year"))
        if year not in purchase_year_map:
            continue  # rinnovo manuale, fee libero
        fee = _to_float(r.get("fee"))
        if fee is None:
            issues.append(f"renewal {year}: fee mancante (atteso={correct_fee})")
        elif abs(fee - correct_fee) > 0.01:
            issues.append(f"renewal {year}: fee errato (atteso={correct_fee}, trovato={fee})")

    # --- 8. start_date/end_date top-level coincidono con l'ultimo renewal ---
    if renewals:
        latest = max(renewals, key=lambda r: _to_int(r.get("year")) or 0)
        latest_year = _to_int(latest.get("year"))
        top_year = parse_membership_year(start_date, end_date)
        if top_year is not None and latest_year is not None and top_year != latest_year:
            issues.append(
                f"start_date top-level è anno {top_year} "
                f"ma il renewal più recente è {latest_year}"
            )

    # --- 9. purchase_id top-level coerente ---
    if top_purchase_id:
        in_purchases = top_purchase_id in purchases
        in_renewals = any(r.get("purchase_id") == top_purchase_id for r in renewals)
        if not in_purchases and not in_renewals:
            issues.append(
                f"purchase_id top-level ({top_purchase_id}) "
                "non trovato né in purchases[] né nei renewals"
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(*, limit: Optional[int], verbose: bool) -> Dict[str, int]:
    scanned = 0
    ok = 0
    with_issues = 0
    issue_counts: Dict[str, int] = defaultdict(int)

    stream = db.collection("memberships").stream()
    for snap in (islice(stream, limit) if limit else stream):
        scanned += 1
        data = snap.to_dict() or {}
        name = f"{data.get('name', '')} {data.get('surname', '')}".strip() or snap.id

        issues = _check(snap.id, data)

        if issues:
            with_issues += 1
            print(f"\n[{snap.id}] {name}")
            for issue in issues:
                print(f"  ✗ {issue}")
                issue_counts[issue.split(":")[0].split("(")[0].strip()] += 1
        elif verbose:
            print(f"[{snap.id}] {name}  ✓")
        else:
            ok += 1

    return {
        "scanned": scanned,
        "ok": ok,
        "with_issues": with_issues,
        "issue_counts": dict(issue_counts),
    }


def main():
    parser = argparse.ArgumentParser(description="Valida coerenza documenti membership.")
    parser.add_argument("--limit", type=int, default=None, help="Limita il numero di membership scansionate.")
    parser.add_argument("--verbose", action="store_true", help="Mostra anche i membri senza problemi.")
    args = parser.parse_args()

    print(f"=== validate_memberships ===")
    print(f"Firestore project : {db.project}")
    print(f"limit={args.limit}\n")

    result = validate(limit=args.limit, verbose=args.verbose)

    print(f"\n{'='*40}")
    print(f"Scansionati : {result['scanned']}")
    print(f"OK          : {result['ok']}")
    print(f"Con problemi: {result['with_issues']}")

    if result["issue_counts"]:
        print("\nProblemi più frequenti:")
        for issue, count in sorted(result["issue_counts"].items(), key=lambda x: -x[1]):
            print(f"  {count:4d}x  {issue}")


if __name__ == "__main__":
    main()
