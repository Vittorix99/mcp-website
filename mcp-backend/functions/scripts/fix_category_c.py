"""
Fix mirato per i 3 membri in Category C dal diagnose_event_memberships:
- acquisto presente ma purchase_id non collegato in renewals né in purchases[].

Per ciascuno:
  1. Aggiunge il purchase_id a purchases[] (ArrayUnion)
  2. Aggiunge un renewal per l'anno del purchase (se non esiste già)

Uso:
  python scripts/fix_category_c.py            # dry-run
  python scripts/fix_category_c.py --apply    # scrive su Firestore
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.firebase_config import db
from google.cloud.firestore_v1 import ArrayUnion

# ---------------------------------------------------------------------------
# Pairs to fix: (membership_id, purchase_id)
# ---------------------------------------------------------------------------
TARGETS = [
    ("RHJun3D6Kdjx3UWaGkoA", "MgGiJITtKlXzW7wODZHA"),   # marcoventi@hotmail.it
    ("YjhPnD9MxqtUSm01SkEf", "Qqc5WAmWHJtSkTNr9QTJ"),   # paoloshakya95@gmail.com
    ("kwNM1LpiR7MK1WfVdpUP", "xZamzgywg2qHKkcJimm1"),   # rcostanza16@gmail.com
]


def _to_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _to_float_or_none(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
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


def _timestamp_to_iso(timestamp: Any) -> Optional[str]:
    if timestamp is None:
        return None
    if hasattr(timestamp, "isoformat"):
        return timestamp.isoformat()
    if hasattr(timestamp, "to_datetime"):
        return timestamp.to_datetime().isoformat()
    if isinstance(timestamp, str):
        return timestamp.strip().replace("Z", "+00:00")
    return None


def fix_pair(membership_id: str, purchase_id: str, apply: bool):
    print(f"\n--- membership={membership_id}  purchase={purchase_id} ---")

    # Load membership
    m_doc = db.collection("memberships").document(membership_id).get()
    if not m_doc.exists:
        print(f"  [ERROR] membership not found")
        return
    m_data = m_doc.to_dict() or {}
    name = f"{m_data.get('name', '')} {m_data.get('surname', '')}".strip()
    email = m_data.get("email", "")
    print(f"  Membro: {name} <{email}>")

    existing_purchases: List[str] = list(m_data.get("purchases") or [])
    existing_renewals: List[Dict] = list(m_data.get("renewals") or [])
    membership_fee = _to_float_or_none(m_data.get("membership_fee"))
    correct_fee = membership_fee if membership_fee is not None else 10.0
    print(f"  purchases[]={existing_purchases}")

    # Stampa dettagli di ogni purchase già in purchases[]
    for pid in existing_purchases:
        doc = db.collection("purchases").document(pid).get()
        if doc.exists:
            d = doc.to_dict() or {}
            participants = d.get("participants") or []
            p_names = [f"{p.get('name','')} {p.get('surname','')} <{p.get('email','')}>".strip() for p in participants]
            print(f"    {pid}  ref_id={d.get('ref_id')}  timestamp={_timestamp_to_iso(d.get('timestamp'))}")
            print(f"      payer={d.get('payer_email')}  amount={d.get('amount_total')}  partecipanti={p_names or '—'}")
        else:
            print(f"    {pid}  [NOT FOUND]")

    print(f"  renewals={[{r.get('year'): r.get('purchase_id')} for r in existing_renewals]}")

    # Load purchase
    p_doc = db.collection("purchases").document(purchase_id).get()
    if not p_doc.exists:
        print(f"  [ERROR] purchase not found")
        return
    p_data = p_doc.to_dict() or {}
    timestamp = p_data.get("timestamp")
    year = _year_from_timestamp(timestamp)
    ts_iso = _timestamp_to_iso(timestamp)
    p_participants = p_data.get("participants") or []
    p_names = [f"{p.get('name','')} {p.get('surname','')} <{p.get('email','')}>".strip() for p in p_participants]
    print(f"  purchase (nuovo)  ref_id={p_data.get('ref_id')}  timestamp={ts_iso}  year={year}")
    print(f"    payer={p_data.get('payer_email')}  amount={p_data.get('amount_total')}  partecipanti={p_names or '—'}")

    if year is None:
        print(f"  [ERROR] cannot determine year from purchase timestamp")
        return

    # Check what needs to be done
    needs_purchases_update = purchase_id not in existing_purchases

    renewal_for_year = next((r for r in existing_renewals if _to_int(r.get("year")) == year), None)
    renewal_exists = renewal_for_year is not None
    renewal_missing_purchase_id = renewal_exists and renewal_for_year.get("purchase_id") is None
    needs_new_renewal = not renewal_exists

    nothing_to_do = (
        not needs_purchases_update
        and not renewal_missing_purchase_id
        and not needs_new_renewal
    )
    if nothing_to_do:
        print(f"  Già tutto OK, niente da fare.")
        return

    if needs_purchases_update:
        print(f"  → Aggiungerà {purchase_id} a purchases[]")
    if renewal_missing_purchase_id:
        print(f"  → Imposterà purchase_id={purchase_id} nel renewal {year} esistente (era None)")
    if needs_new_renewal:
        print(f"  → Creerà renewal anno {year} con purchase_id={purchase_id}")

    if not apply:
        print("  [DRY-RUN] nessuna scrittura")
        return

    updates: Dict[str, Any] = {}

    if needs_purchases_update:
        updates["purchases"] = ArrayUnion([purchase_id])

    if renewal_missing_purchase_id or needs_new_renewal:
        new_renewals = []
        for r in existing_renewals:
            r = dict(r)
            if _to_int(r.get("year")) == year and r.get("purchase_id") is None:
                r["purchase_id"] = purchase_id
                if r.get("fee") is None:
                    r["fee"] = correct_fee
            new_renewals.append(r)
        if needs_new_renewal:
            new_renewals.append({
                "year": year,
                "start_date": ts_iso,
                "end_date": f"31-12-{year}",
                "purchase_id": purchase_id,
                "fee": correct_fee,
            })
        new_renewals = sorted(new_renewals, key=lambda r: _to_int(r.get("year")) or 0)
        existing_years = [_to_int(y) for y in (m_data.get("membership_years") or []) if _to_int(y) is not None]
        new_years = sorted(set(existing_years) | {year})
        updates["renewals"] = new_renewals
        updates["membership_years"] = new_years

    db.collection("memberships").document(membership_id).update(updates)
    print(f"  [OK] Documento aggiornato.")


def main():
    parser = argparse.ArgumentParser(description="Fix mirato per i 3 membri Category C.")
    parser.add_argument("--apply", action="store_true", help="Scrive su Firestore (default: dry-run).")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Firestore project : {db.project}")
    print(f"Mode              : {mode}")
    print(f"Targets           : {len(TARGETS)} membership")

    for membership_id, purchase_id in TARGETS:
        fix_pair(membership_id, purchase_id, apply=args.apply)

    print("\nDone.")
    if not args.apply:
        print("Dry-run: nessuna modifica scritta. Ri-esegui con --apply per persistere.")


if __name__ == "__main__":
    main()
