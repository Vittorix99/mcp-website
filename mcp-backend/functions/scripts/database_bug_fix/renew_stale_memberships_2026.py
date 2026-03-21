"""
Script per identificare e rinnovare i membri del 2025 che hanno acquistato
partecipazione a eventi del 2026 ma non hanno ricevuto la nuova tessera.

Logica di ricerca:
  1. Recupera tutte le membership con start_date nell'anno 2025
  2. Per ognuna controlla se attended_events contiene almeno un evento del 2026
     (cross-reference con la collection events)
  3. Stampa il report (dry-run) oppure esegue il rinnovo completo:
       - Invalida il vecchio pass Pass2U
       - Aggiorna start_date / end_date
       - Pulisce wallet_pass_id / wallet_url
       - Crea nuovo pass
       - Invia la tessera via email

Uso:
  python renew_stale_memberships_2026.py --dry-run   # solo report
  python renew_stale_memberships_2026.py             # esecuzione reale
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
from google.cloud.firestore_v1 import DELETE_FIELD
from utils.events_utils import calculate_end_of_year_membership
from services.memberships.pass2u_service import Pass2UService
from services.communications.mail_service import EmailMessage, mail_service
from utils.templates_mail import get_membership_email_template, get_membership_email_text

CURRENT_YEAR = datetime.now(timezone.utc).year
STALE_YEAR = CURRENT_YEAR - 1  # 2025


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _event_year(event_id: str, cache: dict) -> int | None:
    """Restituisce l'anno dell'evento (da Firestore), con cache per evitare letture duplicate."""
    if event_id in cache:
        return cache[event_id]
    try:
        doc = db.collection("events").document(event_id).get()
        if not doc.exists:
            cache[event_id] = None
            return None
        data = doc.to_dict() or {}
        date_str = data.get("date") or data.get("startDate") or ""
        # Formato atteso: "gg-mm-aaaa" oppure ISO
        if "-" in date_str:
            parts = date_str.split("-")
            if len(parts) == 3:
                # gg-mm-aaaa → anno è l'ultimo
                year = int(parts[2]) if len(parts[2]) == 4 else int(parts[0])
                cache[event_id] = year
                return year
        cache[event_id] = None
        return None
    except Exception as e:
        print(f"    [warn] Impossibile leggere evento {event_id}: {e}")
        cache[event_id] = None
        return None


def _has_current_year_event(attended_events: list, event_cache: dict) -> list:
    """Restituisce la lista degli event_id del CURRENT_YEAR presenti in attended_events."""
    return [
        eid for eid in (attended_events or [])
        if _event_year(eid, event_cache) == CURRENT_YEAR
    ]


def _find_stale_memberships(event_cache: dict) -> list[dict]:
    """
    Cerca tutte le membership con start_date nel STALE_YEAR
    che hanno partecipato ad almeno un evento del CURRENT_YEAR.
    """
    print(f"Ricerca membership con start_date nel {STALE_YEAR}...")
    docs = db.collection("memberships").get()
    stale = []

    for doc in docs:
        data = doc.to_dict() or {}
        start_raw = data.get("start_date") or ""

        # Controlla che start_date sia del 2025
        try:
            start_dt = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
            if start_dt.year != STALE_YEAR:
                continue
        except Exception:
            continue

        # Controlla se ha eventi del 2026
        attended = data.get("attended_events") or []
        events_2026 = _has_current_year_event(attended, event_cache)
        if not events_2026:
            continue

        stale.append({
            "id": doc.id,
            "data": data,
            "events_2026": events_2026,
        })

    return stale


def _renew(membership_id: str, data: dict, events_2026: list, dry_run: bool):
    name = data.get("name", "")
    surname = data.get("surname", "")
    email = data.get("email", "")
    old_pass_id = data.get("wallet_pass_id")
    old_start = data.get("start_date", "N/A")
    membership_sent = data.get("membership_sent", False)

    print(f"\n  Nome:           {name} {surname}")
    print(f"  Email:          {email}")
    print(f"  ID:             {membership_id}")
    print(f"  start_date:     {old_start}")
    print(f"  membership_sent:{membership_sent}")
    print(f"  wallet_pass_id: {old_pass_id or '(nessuno)'}")
    print(f"  Eventi 2026:    {events_2026}")

    if dry_run:
        print("  [DRY-RUN] Nessuna modifica apportata.")
        return

    # 1. Invalida vecchio pass
    if old_pass_id:
        try:
            ok = Pass2UService().invalidate_membership_pass(old_pass_id)
            print(f"  [pass2u] Vecchio pass invalidato: {ok}")
        except Exception as e:
            print(f"  [pass2u] Invalidazione fallita (non bloccante): {e}")

    # 2. Aggiorna date e pulisce campi wallet
    now = datetime.now(timezone.utc)
    new_start = now.isoformat()
    new_end = calculate_end_of_year_membership(now)

    db.collection("memberships").document(membership_id).update({
        "start_date": new_start,
        "end_date": new_end,
        "subscription_valid": True,
        "membership_sent": False,
        "wallet_pass_id": DELETE_FIELD,
        "wallet_url": DELETE_FIELD,
    })
    print(f"  [firestore] Date aggiornate: {new_start} → {new_end}")

    # 3. Crea nuovo pass
    from models import Membership as MembershipModel
    updated_doc = db.collection("memberships").document(membership_id).get()
    updated_data = updated_doc.to_dict() or {}
    membership_model = MembershipModel(
        name=updated_data.get("name", ""),
        surname=updated_data.get("surname", ""),
        email=updated_data.get("email", ""),
        phone=updated_data.get("phone", ""),
        birthdate=updated_data.get("birthdate", ""),
        start_date=updated_data.get("start_date", ""),
        end_date=updated_data.get("end_date", ""),
        subscription_valid=updated_data.get("subscription_valid", True),
        membership_type=updated_data.get("membership_type", "manual"),
        membership_fee=updated_data.get("membership_fee"),
    )

    wallet_url = None
    try:
        wallet = Pass2UService().create_membership_pass(membership_id, membership_model)
        if wallet:
            wallet_url = wallet.wallet_url
            db.collection("memberships").document(membership_id).update({
                "wallet_pass_id": wallet.pass_id,
                "wallet_url": wallet_url,
            })
            print(f"  [pass2u] Nuovo pass creato: {wallet.pass_id}")
        else:
            print("  [pass2u] Creazione pass ha restituito None")
    except Exception as e:
        print(f"  [pass2u] Creazione pass fallita (non bloccante): {e}")

    # 4. Invia email
    if not email:
        print("  [mail] Email mancante, skip invio")
        return

    payload = {k: v for k, v in updated_data.items()}
    payload["membership_id"] = membership_id
    payload["wallet_url"] = wallet_url

    try:
        html_content = get_membership_email_template(payload)
        text_content = get_membership_email_text(payload)
        sent = mail_service.send(EmailMessage(
            to_email=email,
            subject="La tua tessera MCP",
            text_content=text_content,
            html_content=html_content,
            attachment=None,
            category="membership",
        ))
        if sent:
            db.collection("memberships").document(membership_id).update({"membership_sent": True})
            print(f"  [mail] Tessera inviata a {email}")
        else:
            print(f"  [mail] Invio fallito per {email}")
    except Exception as e:
        print(f"  [mail] Errore invio email: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=f"Rinnova membership {STALE_YEAR} con eventi {CURRENT_YEAR}."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview senza modifiche.")
    args = parser.parse_args()

    if args.dry_run:
        print(f"=== DRY-RUN MODE — nessuna modifica verra apportata ===\n")
    else:
        print(f"=== ESECUZIONE REALE ===\n")

    event_cache: dict = {}
    stale = _find_stale_memberships(event_cache)

    if not stale:
        print(f"Nessun membro del {STALE_YEAR} con eventi del {CURRENT_YEAR} trovato.")
        return

    print(f"\nTrovati {len(stale)} membri da rinnovare:\n")

    for entry in stale:
        print(f"[{entry['data'].get('email', entry['id'])}]")
        _renew(entry["id"], entry["data"], entry["events_2026"], dry_run=args.dry_run)

    print("\n=== Fine script ===")


if __name__ == "__main__":
    main()
