"""
Diagnostica discrepanze tra pagamenti di un evento e tessere create.

Per un dato evento classifica ogni purchase e ogni membership in:

  A) Ha pagato MA non ha tessera dell'anno              → membership mancante [BUG]
  B) Ha tessera dell'anno MA non ha pagato questo evento → onorario o rinnovo da altro evento [atteso]
  C) Purchase non tracciato da nessuna parte             → non in renewals NÉ in purchases[] [BUG]
  D) Email duplicate nelle tessere                       → due membership per la stessa email [BUG]
  E) Parità: payers che hanno ottenuto un renewal da questo evento
             vs payers che erano già membri dell'anno (solo ticket)

Uso:
  python scripts/diagnose_event_memberships.py --event-id <EVENT_ID>
  python scripts/diagnose_event_memberships.py --event-id <EVENT_ID> --year 2026
  python scripts/diagnose_event_memberships.py --last-event
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.firebase_config import db
from google.cloud.firestore_v1 import FieldFilter


def _normalize_email(email: Optional[str]) -> str:
    return (email or "").strip().lower()


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def _load_event_purchases(event_id: str) -> List[Dict]:
    snaps = db.collection("purchases").where(filter=FieldFilter("ref_id", "==", event_id)).stream()
    result = []
    for snap in snaps:
        data = snap.to_dict() or {}
        data["id"] = snap.id
        result.append(data)
    return result


def _load_memberships_by_year(year: int) -> List[Dict]:
    snaps = (
        db.collection("memberships")
        .where(filter=FieldFilter("membership_years", "array_contains", year))
        .stream()
    )
    result = []
    for snap in snaps:
        data = snap.to_dict() or {}
        data["id"] = snap.id
        result.append(data)
    return result


def _find_last_event_id() -> Optional[Tuple[str, str]]:
    snaps = (
        db.collection("events")
        .order_by("date", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    for snap in snaps:
        data = snap.to_dict() or {}
        return snap.id, data.get("title", snap.id)
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _renewal_purchase_id_for_year(membership: Dict, year: int) -> Optional[str]:
    """Ritorna il purchase_id del renewal per l'anno dato, o None."""
    for r in (membership.get("renewals") or []):
        if _to_int(r.get("year")) == year:
            return r.get("purchase_id")
    return None


def _has_any_purchase(membership: Dict) -> bool:
    return bool(membership.get("purchase_id") or membership.get("purchases"))


# ---------------------------------------------------------------------------
# Diagnosi
# ---------------------------------------------------------------------------

def diagnose(event_id: str, year: int):
    print(f"\nCarico purchases per evento {event_id}...")
    purchases = _load_event_purchases(event_id)
    print(f"  → {len(purchases)} purchase trovati")

    print(f"Carico membership con anno {year}...")
    memberships = _load_memberships_by_year(year)
    print(f"  → {len(memberships)} membership trovate")

    # Indici
    purchase_by_email: Dict[str, Dict] = {}
    for p in purchases:
        email = _normalize_email(p.get("payer_email"))
        if not email:
            continue
        if email in purchase_by_email:
            print(f"  [WARN] email duplicata nei purchase: {email}")
        else:
            purchase_by_email[email] = p

    membership_by_email: Dict[str, List[Dict]] = defaultdict(list)
    for m in memberships:
        email = _normalize_email(m.get("email"))
        membership_by_email[email].append(m)

    event_purchase_ids: Set[str] = {p["id"] for p in purchases}

    # ---------------------------------------------------------------------------
    # A: ha pagato ma non ha tessera dell'anno [BUG]
    # ---------------------------------------------------------------------------
    paid_no_membership = [
        (email, purchase_by_email[email])
        for email in purchase_by_email
        if email not in membership_by_email
    ]

    # ---------------------------------------------------------------------------
    # B: ha tessera ma non ha pagato questo evento [atteso]
    # Suddiviso in: onorario (nessun purchase) vs rinnovo da altro evento
    # ---------------------------------------------------------------------------
    honorary: List[Tuple] = []
    from_other_event: List[Tuple] = []
    for email, ms in membership_by_email.items():
        if email in purchase_by_email:
            continue
        for m in ms:
            pid_for_year = _renewal_purchase_id_for_year(m, year)
            if pid_for_year is None and not _has_any_purchase(m):
                honorary.append((email, m))
            else:
                from_other_event.append((email, m))

    # ---------------------------------------------------------------------------
    # E: classificazione dei payers
    #   - renewal_from_this_event: il purchase_id è nel renewal dell'anno → membership ottenuta QUI
    #   - ticket_only: ha già la tessera dell'anno da altrove, questo è solo biglietto
    # ---------------------------------------------------------------------------
    renewal_from_this_event: List[Tuple] = []   # (email, purchase_id, membership_id)
    ticket_only: List[Tuple] = []               # (email, purchase_id, membership_id)

    for email, p in purchase_by_email.items():
        pid = p["id"]
        ms = membership_by_email.get(email, [])
        if not ms:
            continue  # già in paid_no_membership
        for m in ms:
            pid_for_year = _renewal_purchase_id_for_year(m, year)
            if pid_for_year == pid:
                renewal_from_this_event.append((email, pid, m["id"]))
            else:
                ticket_only.append((email, pid, m["id"]))

    # ---------------------------------------------------------------------------
    # C: ha pagato questo evento MA il renewal dell'anno non ha purchase_id [BUG]
    #    Significa che il rinnovo è stato creato ma il collegamento al purchase è andato perso.
    #    (non si applica a chi era già membro dell'anno da un altro evento: in quel caso
    #     il renewal esiste già con un purchase_id diverso)
    # ---------------------------------------------------------------------------
    purchase_fully_unlinked: List[Tuple] = []
    for email, p in purchase_by_email.items():
        ms = membership_by_email.get(email, [])
        for m in ms:
            pid_for_year = _renewal_purchase_id_for_year(m, year)
            if pid_for_year is None:
                # Ha un renewal per l'anno ma senza purchase_id → bug
                purchase_fully_unlinked.append((email, p["id"], m["id"]))

    # ---------------------------------------------------------------------------
    # D: email duplicate nelle tessere [BUG]
    # ---------------------------------------------------------------------------
    duplicate_emails = {
        email: ms
        for email, ms in membership_by_email.items()
        if len(ms) > 1
    }

    # ---------------------------------------------------------------------------
    # Report
    # ---------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"RIEPILOGO")
    print(f"{'='*60}")
    print(f"  Purchases evento        : {len(purchases)}")
    print(f"  Membership {year}         : {len(memberships)}")
    non_honorary_count = len(memberships) - len(honorary)
    print(f"  Membership {year} (no onorari): {non_honorary_count}")
    print(f"  Differenza (no onorari) : {non_honorary_count - len(purchases):+d}")
    print()

    # A
    if paid_no_membership:
        print(f"[A] Hanno pagato ma NON hanno tessera {year} ({len(paid_no_membership)}):")
        print(f"    (atteso: hanno pagato per altri senza registrarsi come partecipanti)")
        for email, p in paid_no_membership:
            print(f"    {email}  (purchase: {p['id']}, {p.get('payer_name','')} {p.get('payer_surname','')})")
    else:
        print(f"[A] ✓ Tutti i paganti hanno la tessera {year}")

    print()

    # B
    total_b = len(honorary) + len(from_other_event)
    if total_b:
        print(f"[B] Hanno tessera {year} ma NON hanno pagato questo evento ({total_b}):")
        if honorary:
            print(f"    Onorari ({len(honorary)}):")
            for email, m in honorary:
                print(f"      {email}  (membership: {m['id']}, {m.get('name','')} {m.get('surname','')})")
        if from_other_event:
            print(f"    Rinnovo/altro evento ({len(from_other_event)}):")
            for email, m in from_other_event:
                pid_yr = _renewal_purchase_id_for_year(m, year)
                print(f"      {email}  (membership: {m['id']}, purchase_renewal: {pid_yr or '—'})")
    else:
        print(f"[B] ✓ Tutte le tessere {year} hanno un purchase per questo evento")

    print()

    # C
    if purchase_fully_unlinked:
        print(f"[C] ❌ Renewal {year} senza purchase_id per chi ha pagato questo evento ({len(purchase_fully_unlinked)}) [BUG]:")
        for email, pid, mid in purchase_fully_unlinked:
            print(f"    {email}  purchase={pid}  membership={mid}")
    else:
        print(f"[C] ✓ Tutti i renewal {year} hanno purchase_id per chi ha pagato questo evento")

    print()

    # D
    if duplicate_emails:
        print(f"[D] ❌ Email con più di una membership ({len(duplicate_emails)}) [BUG]:")
        for email, ms in duplicate_emails.items():
            ids = [m["id"] for m in ms]
            print(f"    {email}  → {ids}")
    else:
        print(f"[D] ✓ Nessuna email duplicata")

    print()

    # E
    print(f"[E] PARITÀ PAYERS / RINNOVI:")
    print(f"    Payers che hanno ottenuto tessera da questo evento : {len(renewal_from_this_event)}")
    print(f"    Payers già membri {year} (solo biglietto evento)     : {len(ticket_only)}")
    print(f"    Payers senza tessera {year}                          : {len(paid_no_membership)}")
    print(f"    Totale payers                                      : {len(purchase_by_email)}")
    total_classified = len(renewal_from_this_event) + len(ticket_only) + len(paid_no_membership)
    if total_classified != len(purchase_by_email):
        print(f"    ❌ ERRORE CONTEGGIO: {total_classified} classificati vs {len(purchase_by_email)} payers")
    else:
        print(f"    ✓ Conteggio coerente")

    # Discrepanze E: payers che hanno la tessera ma non tramite questo evento
    if ticket_only:
        print(f"\n    Payers 'solo biglietto' (già avevano tessera {year} da altro evento):")
        for email, pid, mid in ticket_only:
            m = next((m for m in membership_by_email[email] if m["id"] == mid), {})
            pid_yr = _renewal_purchase_id_for_year(m, year)
            print(f"      {email}  purchase={pid}  renewal_{year}_purchase={pid_yr or '—'}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Diagnostica discrepanze pagamenti/tessere per un evento.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--event-id", help="ID dell'evento da analizzare.")
    group.add_argument("--last-event", action="store_true", help="Usa l'ultimo evento trovato.")
    parser.add_argument("--year", type=int, default=None, help="Anno tessere (default: anno corrente).")
    args = parser.parse_args()

    from datetime import datetime
    year = args.year or datetime.now().year

    if args.last_event:
        result = _find_last_event_id()
        if not result:
            print("Nessun evento trovato.")
            return
        event_id, title = result
        print(f"Ultimo evento: {title} ({event_id})")
    else:
        event_id = args.event_id

    print(f"Firestore project : {db.project}")
    print(f"Evento            : {event_id}")
    print(f"Anno tessere      : {year}")

    diagnose(event_id, year)


if __name__ == "__main__":
    main()
