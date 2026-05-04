"""
Script one-shot per rinnovare le membership di soci che hanno acquistato
il ticket oggi (17/03/2026) ma non hanno ricevuto la nuova tessera a causa
del bug nel controllo ConflictError (ora fixato).

Operazioni per ogni email:
  1. Trova la membership esistente
  2. Invalida il vecchio wallet pass su Pass2U
  3. Aggiorna start_date / end_date e azzera wallet_pass_id / wallet_url
  4. Crea un nuovo wallet pass
  5. Invia la tessera via email

Uso:
  python renew_memberships_2026.py --dry-run     # solo preview
  python renew_memberships_2026.py               # esecuzione reale
"""

import argparse
import os
import sys
from datetime import datetime, timezone

# Usa il service account di produzione prima di qualsiasi import Firebase
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "/Users/vittoriodigiorgio/Desktop/MCP-WEB-PROJECT/mcp-backend/functions/service_account.json"
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db
from google.cloud.firestore_v1 import DELETE_FIELD, FieldFilter
from utils.events_utils import calculate_end_of_year_membership
from services.memberships.pass2u_service import Pass2UService
from services.communications.mail_service import EmailMessage, mail_service
from utils.templates_mail import get_membership_email_template, get_membership_email_text

EMAILS_TO_RENEW = [
    "maria_beatrice.mocciaro@edu.escp.eu",
    "sofia.abbadessa@gmail.com",
    "cristina.ruisij@gmail.com",
    "enricusumano@gmail.com",
    "andreatortorici11@gmail.com",
]


def find_membership_by_email(email: str):
    docs = db.collection("memberships").where(filter=FieldFilter("email", "==", email)).limit(1).get()
    if not docs:
        return None, None
    doc = docs[0]
    return doc.id, doc.to_dict() or {}


def _create_pass_and_send(membership_id: str, data: dict):
    """Crea il pass Pass2U e invia l'email senza aggiornare le date (già nel 2026)."""
    from models import Membership as MembershipModel

    email = data.get("email", "")
    fresh_doc = db.collection("memberships").document(membership_id).get()
    fresh_data = fresh_doc.to_dict() or {}

    membership_model = MembershipModel(
        name=fresh_data.get("name", ""),
        surname=fresh_data.get("surname", ""),
        email=fresh_data.get("email", ""),
        phone=fresh_data.get("phone", ""),
        birthdate=fresh_data.get("birthdate", ""),
        start_date=fresh_data.get("start_date", ""),
        end_date=fresh_data.get("end_date", ""),
        subscription_valid=fresh_data.get("subscription_valid", True),
        membership_type=fresh_data.get("membership_type", "manual"),
        membership_fee=fresh_data.get("membership_fee"),
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
            print(f"  [pass2u] Pass creato: {wallet.pass_id}")
        else:
            print("  [pass2u] Creazione pass ha restituito None")
    except Exception as e:
        print(f"  [pass2u] Creazione pass fallita (non bloccante): {e}")

    if not email:
        print("  [mail] Email mancante, skip invio")
        return

    payload = {k: v for k, v in fresh_data.items()}
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


def renew(membership_id: str, data: dict, dry_run: bool):
    name = data.get("name", "")
    surname = data.get("surname", "")
    email = data.get("email", "")
    old_pass_id = data.get("wallet_pass_id")
    old_start = data.get("start_date", "N/A")

    print(f"\n  Nome:          {name} {surname}")
    print(f"  Email:         {email}")
    print(f"  ID membership: {membership_id}")
    print(f"  start_date:    {old_start}")
    print(f"  wallet_pass_id: {old_pass_id or '(nessuno)'}")

    # Controlla se la membership è già nel 2026
    current_year = datetime.now(timezone.utc).year
    try:
        start_year = datetime.fromisoformat(str(old_start).replace("Z", "+00:00")).year
    except Exception:
        start_year = None

    if start_year == current_year:
        if not old_pass_id:
            print(f"  [INFO] start_date già nel {current_year} ma pass mancante — creo solo il pass e invio email.")
            if dry_run:
                print("  [DRY-RUN] Nessuna modifica apportata.")
                return
            _create_pass_and_send(membership_id, data)
        else:
            print(f"  [SKIP] start_date già nel {current_year} e pass presente — nessuna azione necessaria.")
        return

    if dry_run:
        print("  [DRY-RUN] Nessuna modifica apportata.")
        return

    # 1. Invalida il vecchio pass
    if old_pass_id:
        try:
            ok = Pass2UService().invalidate_membership_pass(old_pass_id)
            print(f"  [pass2u] Vecchio pass invalidato: {ok}")
        except Exception as e:
            print(f"  [pass2u] Invalidazione fallita (non bloccante): {e}")

    # 2. Aggiorna date e pulisce i campi wallet
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
    print(f"  [firestore] Date aggiornate: {new_start} -> {new_end}")

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

    # 4. Invia email con la nuova tessera
    if not email:
        print("  [mail] Nessuna email presente, skip invio")
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


def main():
    parser = argparse.ArgumentParser(description="Rinnova membership 2026 per soci con acquisto del 17/03/2026.")
    parser.add_argument("--dry-run", action="store_true", help="Preview senza modifiche.")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY-RUN MODE: nessuna modifica verra apportata ===\n")
    else:
        print("=== ESECUZIONE REALE ===\n")

    for email in EMAILS_TO_RENEW:
        print(f"[{email}]")
        membership_id, data = find_membership_by_email(email)

        if not membership_id:
            print(f"  ATTENZIONE: membership non trovata per {email}")
            continue

        renew(membership_id, data, dry_run=args.dry_run)

    print("\n=== Fine script ===")


if __name__ == "__main__":
    main()
