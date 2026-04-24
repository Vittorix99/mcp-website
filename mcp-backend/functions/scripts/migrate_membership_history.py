"""
Backfill storico membership (`renewals`, `membership_years`) per documenti legacy.

Rispetto alla versione precedente, questa versione risolve il problema del purchase_id:
invece di copiare il campo top-level (congelato al primo acquisto) su tutti gli anni,
legge ogni documento in `purchases[]`, ricava l'anno dal timestamp e assegna il
purchase_id corretto al renewal dell'anno corrispondente.

Logica per purchase_id:
  - Legge tutti i doc in `purchases[]` + il top-level `purchase_id`
  - Costruisce una mappa {anno: purchase_id} (primo acquisto per quell'anno)
  - Ogni renewal riceve il purchase_id del suo anno specifico
  - Se per quell'anno non esiste un purchase (rinnovo manuale) → purchase_id=None

Uso:
  # Preview (default, non scrive)
  python scripts/migrate_membership_history.py

  # Solo documenti con renewals/membership_years mancanti
  python scripts/migrate_membership_history.py --only-missing --apply

  # Tutti i documenti (normalizza anche chi ha già renewals con purchase_id sbagliati)
  python scripts/migrate_membership_history.py --apply

  # Test su subset
  python scripts/migrate_membership_history.py --limit 20
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from itertools import islice
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.firebase_config import db
from domain.membership_rules import dedupe_renewals_by_year, parse_membership_year


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _iter_limited(stream, limit: Optional[int]):
    if limit is None:
        yield from stream
        return
    yield from islice(stream, limit)


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float_or_none(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _year_from_timestamp(timestamp: Any) -> Optional[int]:
    """Estrae l'anno da un timestamp PayPal (stringa ISO) o Firestore Timestamp."""
    if timestamp is None:
        return None
    # Firestore Timestamp object
    if hasattr(timestamp, "year"):
        return int(timestamp.year)
    if hasattr(timestamp, "to_datetime"):
        return timestamp.to_datetime().year
    # Stringa ISO da PayPal: "2025-03-01T10:00:00Z"
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.strip().replace("Z", "+00:00")).year
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Purchase year map
# ---------------------------------------------------------------------------

def _timestamp_to_iso(timestamp: Any) -> Optional[str]:
    """Converte un timestamp Firestore o stringa ISO in stringa ISO normalizzata."""
    if timestamp is None:
        return None
    if hasattr(timestamp, "isoformat"):
        return timestamp.isoformat()
    if hasattr(timestamp, "to_datetime"):
        return timestamp.to_datetime().isoformat()
    if isinstance(timestamp, str):
        return timestamp.strip().replace("Z", "+00:00")
    return None


def _build_purchase_year_map(purchase_ids: List[str]) -> Dict[int, Dict[str, Any]]:
    """
    Legge i documenti purchase e ritorna:
      { anno: { "purchase_id": ..., "timestamp_iso": ..., "fee": ... } }
    Se più acquisti cadono nello stesso anno, conserva il primo trovato.
    """
    if not purchase_ids:
        return {}

    result: Dict[int, Dict[str, Any]] = {}
    for pid in purchase_ids:
        doc = db.collection("purchases").document(pid).get()
        if not doc.exists:
            print(f"    [WARN] purchase/{pid} non trovato in Firestore")
            continue
        data = doc.to_dict() or {}
        timestamp = data.get("timestamp")
        year = _year_from_timestamp(timestamp)
        if year is None:
            print(f"    [WARN] purchase/{pid}: timestamp assente o non parsabile")
            continue
        if year not in result:
            result[year] = {
                "purchase_id": pid,
                "timestamp_iso": _timestamp_to_iso(timestamp),
                "fee": None,
            }

    return result


# ---------------------------------------------------------------------------
# Renewal canonicalization
# ---------------------------------------------------------------------------

def _normalize_renewal_entry(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    year = _to_int(raw.get("year"))
    if year is None:
        year = parse_membership_year(raw.get("start_date"), raw.get("end_date"))
    if year is None:
        return None
    return {
        "year": year,
        "start_date": raw.get("start_date"),
        "end_date": raw.get("end_date"),
        "purchase_id": raw.get("purchase_id"),
        "fee": _to_float_or_none(raw.get("fee")),
    }


def _canonicalize_renewals(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = [_normalize_renewal_entry(e) for e in entries]
    cleaned = [e for e in cleaned if e is not None]
    deduped = dedupe_renewals_by_year(cleaned)
    return sorted(deduped, key=lambda item: int(item.get("year", 0)))


def _canonicalize_years(values) -> List[int]:
    years = {_to_int(v) for v in values}
    return sorted(y for y in years if y is not None)


# ---------------------------------------------------------------------------
# Core update builder
# ---------------------------------------------------------------------------

def _build_updates(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    top_purchase_id = data.get("purchase_id")   # congelato al primo acquisto
    membership_fee = _to_float_or_none(data.get("membership_fee"))

    # Costruisce la mappa anno→{purchase_id, timestamp_iso, fee} dai documenti reali
    purchase_ids: List[str] = list(data.get("purchases") or [])
    if top_purchase_id and top_purchase_id not in purchase_ids:
        purchase_ids = [top_purchase_id] + purchase_ids
    purchase_year_map = _build_purchase_year_map(purchase_ids)

    # Normalizza renewals esistenti
    existing_renewals = _canonicalize_renewals(data.get("renewals") or [])
    by_year: Dict[int, Dict[str, Any]] = {
        int(r["year"]): dict(r) for r in existing_renewals if r.get("year") is not None
    }

    # Assicura che l'anno del top-level (start_date corrente) sia rappresentato
    top_year = parse_membership_year(start_date, end_date)
    if top_year is not None and top_year not in by_year:
        by_year[top_year] = {
            "year": top_year,
            "start_date": start_date,
            "end_date": end_date,
            "purchase_id": None,
            "fee": membership_fee,
        }
    elif top_year is not None:
        current = by_year[top_year]
        if not current.get("start_date") and start_date:
            current["start_date"] = start_date
        if not current.get("end_date") and end_date:
            current["end_date"] = end_date
        if current.get("fee") is None and membership_fee is not None:
            current["fee"] = membership_fee

    # Aggiunge un renewal per ogni anno con un purchase che non è già presente.
    # Usa timestamp del purchase come start_date e "31-12-YYYY" come end_date.
    for year, info in purchase_year_map.items():
        if year not in by_year:
            by_year[year] = {
                "year": year,
                "start_date": info["timestamp_iso"],
                "end_date": f"31-12-{year}",
                "purchase_id": info["purchase_id"],
                "fee": membership_fee,
            }

    # Applica il purchase_id corretto dalla mappa a tutti i renewal
    for year, renewal in by_year.items():
        if year in purchase_year_map:
            renewal["purchase_id"] = purchase_year_map[year]["purchase_id"]
        # Anno senza purchase (rinnovo manuale) → purchase_id rimane invariato

    renewals = _canonicalize_renewals(list(by_year.values()))

    existing_years = _canonicalize_years(data.get("membership_years") or [])
    renewal_years = _canonicalize_years([r.get("year") for r in renewals])
    years = sorted({*existing_years, *renewal_years})

    updates: Dict[str, Any] = {}
    if renewals != existing_renewals:
        updates["renewals"] = renewals
    if years != existing_years:
        updates["membership_years"] = years

    debug = {
        "existing_renewals": existing_renewals,
        "new_renewals": renewals,
        "existing_years": existing_years,
        "new_years": years,
        "purchase_year_map": {y: info["purchase_id"] for y, info in purchase_year_map.items()},
    }
    return updates, debug


# ---------------------------------------------------------------------------
# Fee fix (one-shot correction for renewals written with wrong fee)
# ---------------------------------------------------------------------------

def fix_fees(*, apply: bool, limit: Optional[int]) -> Dict[str, int]:
    """
    Corregge il campo `fee` nei renewal esistenti usando `membership_fee`
    dal documento membership (fallback 10.0).
    Tocca solo renewals con purchase_id presente (rinnovi da PayPal).
    Non richiede di caricare i documenti purchase.
    """
    scanned = 0
    changed = 0
    written = 0

    batch = db.batch()
    batch_writes = 0

    stream = db.collection("memberships").stream()
    for snap in _iter_limited(stream, limit):
        scanned += 1
        data = snap.to_dict() or {}

        renewals = data.get("renewals") or []
        if not renewals:
            continue

        membership_fee = _to_float_or_none(data.get("membership_fee"))
        correct_fee = membership_fee if membership_fee is not None else 10.0

        new_renewals = []
        any_changed = False
        for r in renewals:
            r = dict(r)
            # Only fix paid renewals (those with a purchase_id)
            if r.get("purchase_id") and r.get("fee") != correct_fee:
                r["fee"] = correct_fee
                any_changed = True
            new_renewals.append(r)

        if not any_changed:
            continue

        changed += 1
        name = f"{data.get('name', '')} {data.get('surname', '')}".strip()
        print(f"[{snap.id}] {name} → fee corretto a {correct_fee} €")

        if not apply:
            continue

        batch.update(snap.reference, {"renewals": new_renewals})
        batch_writes += 1
        written += 1

        if batch_writes >= 400:
            batch.commit()
            batch = db.batch()
            batch_writes = 0

    if apply and batch_writes > 0:
        batch.commit()

    return {"scanned": scanned, "changed": changed, "written": written if apply else 0}


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------

def migrate_membership_history(
    *, apply: bool, only_missing: bool, limit: Optional[int]
) -> Dict[str, int]:
    scanned = 0
    changed = 0
    written = 0

    batch = db.batch()
    batch_writes = 0

    stream = db.collection("memberships").stream()
    for snap in _iter_limited(stream, limit):
        scanned += 1
        data = snap.to_dict() or {}

        if only_missing:
            has_renewals = bool(data.get("renewals"))
            has_years = bool(data.get("membership_years"))
            if has_renewals and has_years:
                continue

        updates, debug = _build_updates(data)
        if not updates:
            continue
        changed += 1

        name = f"{data.get('name', '')} {data.get('surname', '')}".strip()
        print(
            f"[{snap.id}] {name}\n"
            f"  purchase_map : {debug['purchase_year_map']}\n"
            f"  renewals     : {len(debug['existing_renewals'])} → {len(debug['new_renewals'])}\n"
            f"  years        : {debug['existing_years']} → {debug['new_years']}\n"
            f"  renewal ids  : { {r['year']: r.get('purchase_id') for r in debug['new_renewals']} }"
        )

        if not apply:
            continue

        batch.update(snap.reference, updates)
        batch_writes += 1
        written += 1

        if batch_writes >= 400:
            batch.commit()
            batch = db.batch()
            batch_writes = 0

    if apply and batch_writes > 0:
        batch.commit()

    return {"scanned": scanned, "changed": changed, "written": written if apply else 0}


def main():
    parser = argparse.ArgumentParser(
        description="Backfill renewals/membership_years con purchase_id corretti per anno."
    )
    parser.add_argument("--apply", action="store_true", help="Scrive su Firestore (default: dry-run).")
    parser.add_argument("--only-missing", action="store_true", help="Solo doc senza renewals o membership_years.")
    parser.add_argument("--fix-fees", action="store_true", help="Corregge solo il fee nei renewal esistenti.")
    parser.add_argument("--limit", type=int, default=None, help="Limita il numero di membership scansionate.")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Firestore project : {db.project}\n")

    if args.fix_fees:
        print(f"=== fix_fees ({mode}) ===")
        result = fix_fees(apply=args.apply, limit=args.limit)
    else:
        print(f"=== migrate_membership_history ({mode}) ===")
        print(f"only_missing={args.only_missing}  limit={args.limit}\n")
        result = migrate_membership_history(
            apply=args.apply,
            only_missing=args.only_missing,
            limit=args.limit,
        )

    print(
        f"\nDone. scanned={result['scanned']}  changed={result['changed']}  written={result['written']}"
    )
    if not args.apply:
        print("Dry-run: nessuna modifica scritta. Ri-esegui con --apply per persistere.")


if __name__ == "__main__":
    main()
