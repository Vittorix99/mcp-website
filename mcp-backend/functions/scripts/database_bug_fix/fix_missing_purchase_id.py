"""
Script per correggere le membership prive di purchase_id.

Logica:
  1. Scansiona tutte le membership dove purchase_id è assente o vuoto
  2. Per ognuna legge l'array purchases (lista di purchase_id)
  3. Recupera il timestamp di ciascun purchase e prende quello più vecchio
  4. Imposta purchase_id = id del purchase più vecchio

Uso:
  python fix_missing_purchase_id.py --dry-run   # solo report
  python fix_missing_purchase_id.py             # esecuzione reale
"""

import argparse
import os
import sys
from datetime import datetime, timezone

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "/Users/vittoriodigiorgio/Desktop/MCP-WEB-PROJECT/mcp-backend/functions/service_account.json"
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db


def _parse_timestamp(ts) -> datetime:
    """Normalizza il timestamp di un purchase in un datetime comparabile."""
    if ts is None:
        return datetime.max.replace(tzinfo=timezone.utc)
    if hasattr(ts, "timestamp"):
        # google.cloud.firestore Timestamp
        return ts.astimezone(timezone.utc) if hasattr(ts, "astimezone") else datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
    if isinstance(ts, datetime):
        return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.max.replace(tzinfo=timezone.utc)


def _find_first_purchase_id(purchase_ids: list) -> tuple[str | None, str | None]:
    """
    Dato un array di purchase_id, recupera i documenti, li ordina per timestamp
    e restituisce (purchase_id_più_vecchio, timestamp_stringa).
    """
    candidates = []
    for pid in purchase_ids:
        if not pid:
            continue
        try:
            doc = db.collection("purchases").document(pid).get()
            if not doc.exists:
                print(f"    [warn] Purchase {pid} non trovato in Firestore")
                continue
            data = doc.to_dict() or {}
            ts = _parse_timestamp(data.get("timestamp"))
            candidates.append((ts, pid))
        except Exception as e:
            print(f"    [warn] Errore lettura purchase {pid}: {e}")

    if not candidates:
        return None, None

    candidates.sort(key=lambda x: x[0])
    first_ts, first_id = candidates[0]
    ts_str = first_ts.isoformat() if first_ts != datetime.max.replace(tzinfo=timezone.utc) else "N/A"
    return first_id, ts_str


def main():
    parser = argparse.ArgumentParser(description="Fix purchase_id mancante nelle membership.")
    parser.add_argument("--dry-run", action="store_true", help="Preview senza modifiche.")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY-RUN MODE — nessuna modifica verra apportata ===\n")
    else:
        print("=== ESECUZIONE REALE ===\n")

    docs = db.collection("memberships").get()

    fixed = 0
    skipped = 0
    errors = 0

    for doc in docs:
        data = doc.to_dict() or {}
        membership_id = doc.id

        # Salta chi ha già purchase_id
        if data.get("purchase_id"):
            skipped += 1
            continue

        purchases = data.get("purchases") or []
        if not purchases:
            print(f"[{membership_id}] {data.get('email', '?')} — nessun purchase, skip")
            skipped += 1
            continue

        first_id, first_ts = _find_first_purchase_id(purchases)

        if not first_id:
            print(f"[{membership_id}] {data.get('email', '?')} — purchases presenti ma non recuperabili")
            errors += 1
            continue

        print(
            f"[{membership_id}] {data.get('name', '')} {data.get('surname', '')} "
            f"<{data.get('email', '?')}>"
        )
        print(f"  purchases:         {purchases}")
        print(f"  primo purchase:    {first_id}  (timestamp: {first_ts})")

        if args.dry_run:
            print("  [DRY-RUN] Nessuna modifica apportata.")
        else:
            try:
                db.collection("memberships").document(membership_id).update({
                    "purchase_id": first_id,
                })
                print(f"  [firestore] purchase_id impostato: {first_id}")
                fixed += 1
            except Exception as e:
                print(f"  [errore] {e}")
                errors += 1

    print(f"\n=== Fine script ===")
    print(f"  Fixati:   {fixed}")
    print(f"  Skippati: {skipped}")
    print(f"  Errori:   {errors}")


if __name__ == "__main__":
    main()
