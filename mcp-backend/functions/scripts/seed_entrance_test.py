#!/usr/bin/env python3
"""
Entrance Scanner — Test Data Seed
==================================

Popola il Firestore emulator con tutti i dati necessari per testare
la logica di ingresso con le tessere reali di Vittorio Di Giorgio
e una batteria di utenti seedati con email plus-addressed su mcpweb.test.

Scenari coperti
---------------
  1. 2 tessere di Vittorio Di Giorgio → membership valida + partecipante → "valid"
  2. 8 membri extra con ticket evento → membership valida + partecipante → "valid"
  3. 5 membri extra senza ticket evento → "invalid_no_purchase"
  4. 1 membro partecipante già scansionato → "already_scanned"
  5. Tutte le email seedate usano plus addressing su mcpweb.test@gmail.com
  6. (tessera inesistente) → nessun documento → "invalid_member_not_found"

PRE-REQUISITO
  firebase emulators:start --only firestore
  oppure
  export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080

USO
  cd mcp-backend/functions
  python scripts/seed_entrance_test.py [--reset] [--pass-csv /path/to/Pass_Data.csv]

  --reset   elimina tutti i documenti creati da questo script prima di riseedare
  --pass-csv  CSV Pass2U con colonne passId/barcode-NFC per associare wallet ai membri
"""

import argparse
import csv
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Punta sull'emulator se l'env non è già impostato ──────────────────────────
if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"

import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

# ── Init Firebase Admin (emulator-safe, senza ADC locali) ──────────────────────
def _resolve_credentials_path() -> Path:
    raw_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "./service_account_test.json"
    candidate = Path(raw_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    functions_dir = Path(__file__).resolve().parents[1]
    for path in ((Path.cwd() / candidate), (functions_dir / candidate)):
        resolved = path.resolve()
        if resolved.exists():
            return resolved

    raise FileNotFoundError(f"Firebase credentials file not found: {raw_path}")


if not firebase_admin._apps:
    cred_path = _resolve_credentials_path()
    project_id = (
        os.environ.get("GCLOUD_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or "mcp-website-dev-39539"
    )
    firebase_admin.initialize_app(
        credentials.Certificate(str(cred_path)),
        {"projectId": project_id},
    )

db = admin_firestore.client()

BASE_TEST_EMAIL = os.environ.get("ENTRANCE_TEST_EMAIL_BASE", "mcpweb.test@gmail.com")
DEFAULT_PASS_CSV_CANDIDATES = (
    Path.home() / "Downloads" / "Pass_Data.csv",
    Path(__file__).resolve().parents[3] / "Pass_Data.csv",
    Path(__file__).resolve().parents[1] / "Pass_Data.csv",
)


def _split_email(email: str):
    value = (email or "").strip().lower()
    if "@" not in value:
        raise ValueError(f"Invalid base email: {email}")
    local, domain = value.split("@", 1)
    if not local or not domain:
        raise ValueError(f"Invalid base email: {email}")
    return local, domain


def _plus_email(prefix: str, index: int) -> str:
    local, domain = _split_email(BASE_TEST_EMAIL)
    safe_prefix = (prefix or "entrance_test").strip().replace(" ", "_").lower()
    return f"{local}+{safe_prefix}_{index:02d}@{domain}"


def _clean_csv_cell(raw: str) -> str:
    value = (raw or "").strip()
    if value.startswith('="') and value.endswith('"'):
        value = value[2:-1]
    return value.strip().strip('"').strip()


def _resolve_pass_csv_path(explicit_path: str | None) -> Path:
    if explicit_path:
        path = Path(explicit_path).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"Pass CSV file not found: {path}")

    env_path = os.environ.get("ENTRANCE_PASS_CSV")
    if env_path:
        path = Path(env_path).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"Pass CSV file not found: {path}")

    for candidate in DEFAULT_PASS_CSV_CANDIDATES:
        if candidate.exists():
            return candidate

    searched = ", ".join(str(path) for path in DEFAULT_PASS_CSV_CANDIDATES)
    raise FileNotFoundError(
        "Pass CSV file not found. Provide --pass-csv or ENTRANCE_PASS_CSV. "
        f"Searched: {searched}"
    )


def _load_pass_lookup(csv_path: Path):
    lookup = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            membership_id = _clean_csv_cell(row.get("barcode/NFC", ""))
            pass_id = _clean_csv_cell(row.get("passId", ""))
            if not membership_id or not pass_id:
                continue

            if membership_id in lookup:
                continue

            wallet_url = f"https://www.pass2u.net/d/{pass_id}"
            lookup[membership_id] = {
                "wallet_pass_id": pass_id,
                "wallet_url": wallet_url,
                "wallet_name": _clean_csv_cell(row.get("name(Name)", "")),
                "wallet_validity": _clean_csv_cell(row.get("validity(Validity)", "")),
                "wallet_mail": _clean_csv_cell(row.get("mail(Mail)", "")),
            }
    return lookup

# ─────────────────────────────────────────────────────────────────────────────
# Dati fissi
# ─────────────────────────────────────────────────────────────────────────────

# Tessere reali di Vittorio Di Giorgio (dagli screenshot)
REAL_MEMBER_IDS = {
    "KmSbPtCkafBLaoF9zGr4": {
        "name": "Vittorio",
        "surname": "Di Giorgio",
        "email": _plus_email("entrance_vittorio", 1),
        "phone": "+393401234567",
        "birthdate": "01-01-1998",
        "subscription_valid": True,
        "end_date": "01-01-2027",
        "start_date": "01-01-2026",
        "membership_sent": True,
        "membership_type": "standard",
    },
    "HIWVbeT2RfjSv9jZGY9y": {
        "name": "Vittorio",
        "surname": "Di Giorgio",
        "email": _plus_email("entrance_vittorio", 2),
        "phone": "+393401234568",
        "birthdate": "01-01-1998",
        "subscription_valid": True,
        "end_date": "01-01-2027",
        "start_date": "01-01-2026",
        "membership_sent": True,
        "membership_type": "standard",
    },
}

# Membri di test aggiuntivi (ID generati deterministicamente per riproducibilità)
ATTENDING_MEMBER_SPECS = [
    ("Aq7MxK2pLd9VrT6HnCb1", "Giulia", "Rossi", "15-06-1995", "+393500000001"),
    ("Bw4NzJ8sQe1YpU5KfDm2", "Luca", "Bianchi", "20-03-1993", "+393500000002"),
    ("Cx6PtR3mHg8LaV2JnEs4", "Chiara", "Esposito", "08-11-1997", "+393500000003"),
    ("Dv9KsT5qWp2MbX7RhFu6", "Marco", "Ricci", "12-01-1994", "+393500000004"),
    ("test_attendee_005", "Sara", "Conti", "27-09-1996", "+393500000005"),
    ("Fz5MvX1pSd7JkB3YnHa9", "Davide", "Romano", "03-07-1992", "+393500000006"),
    ("Gp8NwQ4rTf1LmC6ZoIb3", "Elena", "Gallo", "18-04-1998", "+393500000007"),
    ("Hq3PxR6sUg9VnD2AkJc5", "Federico", "Moretti", "30-12-1991", "+393500000008"),
]

NON_ATTENDING_MEMBER_SPECS = [
    ("Ir6QyT9vHb3WpE7LmKd1", "Mario", "Rossi", "15-06-1995", "+393500000101"),
    ("Js9RzU2wNc6XqF4PnLe8", "Anna", "Marino", "09-02-1990", "+393500000102"),
    ("Kt2SvV5xPd8YrG1QoMf6", "Paolo", "Greco", "11-08-1989", "+393500000103"),
    ("Lu5TwW8yQf1ZsH3RpNg9", "Marta", "Lombardi", "24-05-1997", "+393500000104"),
    ("Mv8UxX2zRg4AtJ6SqOh7", "Simone", "Barbieri", "06-10-1994", "+393500000105"),
]


def _build_members(specs, prefix: str):
    members = {}
    for index, (member_id, name, surname, birthdate, phone) in enumerate(specs, start=1):
        members[member_id] = {
            "name": name,
            "surname": surname,
            "email": _plus_email(prefix, index),
            "phone": phone,
            "birthdate": birthdate,
            "subscription_valid": True,
            "end_date": "01-01-2027",
            "start_date": "01-01-2026",
            "membership_sent": False,
            "membership_type": "standard",
        }
    return members


ATTENDING_MEMBERS = _build_members(ATTENDING_MEMBER_SPECS, "entrance_attendee")
NON_ATTENDING_MEMBERS = _build_members(NON_ATTENDING_MEMBER_SPECS, "entrance_member_only")
EXTRA_MEMBERS = {**ATTENDING_MEMBERS, **NON_ATTENDING_MEMBERS}
PRE_SCANNED_MEMBER_ID = "Bw4NzJ8sQe1YpU5KfDm2"

ALL_MEMBER_IDS = list(REAL_MEMBER_IDS.keys()) + list(EXTRA_MEMBERS.keys())

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print(msg: str, icon: str = "•"):
    print(f"  {icon}  {msg}")


def _delete_if_exists(ref):
    try:
        ref.delete()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Reset
# ─────────────────────────────────────────────────────────────────────────────

def reset(event_id: str, token: str):
    print("\n🗑  Reset documenti precedenti...")

    for mid in ALL_MEMBER_IDS:
        _delete_if_exists(db.collection("memberships").document(mid))

    # Partecipanti
    participants = db.collection("participants").document(event_id).collection("participants_event").stream()
    for doc in participants:
        doc.reference.delete()

    # Scan token
    if token:
        _delete_if_exists(db.collection("scan_tokens").document(token))

    # Entrance scans
    scans = db.collection("entrance_scans").document(event_id).collection("scans").stream()
    for doc in scans:
        doc.reference.delete()

    # Evento
    _delete_if_exists(db.collection("events").document(event_id))

    _print("Reset completato", "✓")


# ─────────────────────────────────────────────────────────────────────────────
# Seed
# ─────────────────────────────────────────────────────────────────────────────

def seed(pass_lookup):
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    event_date_str = tomorrow.strftime("%d-%m-%Y")
    token = secrets.token_hex(16)
    expires_at = now + timedelta(hours=12)

    print("\n🌱  Creazione dati di test...")

    # ── 1. Evento ─────────────────────────────────────────────────────────────
    event_ref = db.collection("events").document()
    event_id = event_ref.id
    event_ref.set({
        "title": "MCP Entrance Test Night",
        "date": event_date_str,
        "startTime": "22:00",
        "endTime": "04:00",
        "location": "Test Venue",
        "locationHint": "Ingresso principale",
        "price": 15.0,
        "status": "active",
        "participantsCount": 0,
        "createdAt": admin_firestore.SERVER_TIMESTAMP,
    })
    _print(f"Evento creato: {event_id}", "✓")

    # ── 2. Scan token ─────────────────────────────────────────────────────────
    db.collection("scan_tokens").document(token).set({
        "event_id": event_id,
        "created_by": "seed_script",
        "created_at": admin_firestore.SERVER_TIMESTAMP,
        "expires_at": expires_at,
        "is_active": True,
    })
    _print(f"Scan token: {token}", "✓")
    _print(f"Scade alle: {expires_at.strftime('%H:%M')} UTC", " ")

    # ── 3. Membership price ───────────────────────────────────────────────────
    year = str(now.year)
    db.collection("membership_settings").document("price").set(
        {"price_by_year": {year: 10.0}},
        merge=True,
    )
    _print(f"Prezzo membership {year}: 10.0€", "✓")

    # ── 4. Membri ─────────────────────────────────────────────────────────────
    all_members = {**REAL_MEMBER_IDS, **EXTRA_MEMBERS}
    missing_pass_data = []
    for mid, data in all_members.items():
        wallet = pass_lookup.get(mid)
        if wallet:
            data["wallet_pass_id"] = wallet["wallet_pass_id"]
            data["wallet_url"] = wallet["wallet_url"]
            data["membership_sent"] = True
            data["wallet_name"] = wallet["wallet_name"]
            data["wallet_validity"] = wallet["wallet_validity"]
            data["wallet_mail"] = wallet["wallet_mail"]
        else:
            missing_pass_data.append(mid)
        db.collection("memberships").document(mid).set(data)
    _print(f"{len(all_members)} membri scritti in Firestore", "✓")
    _print(f"{len(all_members) - len(missing_pass_data)} membri con wallet già associato", "✓")

    # ── 5. Partecipanti ───────────────────────────────────────────────────────
    # I due Vittorio + 8 membri di test hanno il biglietto evento
    participants_to_add = [
        *[(mid, data) for mid, data in REAL_MEMBER_IDS.items()],
        *[(mid, data) for mid, data in ATTENDING_MEMBERS.items()],
    ]
    participant_ids = []
    for mid, data in participants_to_add:
        p_ref = db.collection("participants").document(event_id).collection("participants_event").document()
        p_ref.set({
            "membershipId": mid,
            "name": data["name"],
            "surname": data["surname"],
            "email": data["email"],
            "phone": data["phone"],
            "birthdate": data["birthdate"],
            "price": 15.0,
            "payment_method": "cash",
            "ticket_sent": False,
            "location_sent": False,
            "membership_included": True,
            "createdAt": admin_firestore.SERVER_TIMESTAMP,
        })
        participant_ids.append((mid, p_ref.id))
    _print(f"{len(participant_ids)} partecipanti creati", "✓")

    # ── 6. Pre-scansiona un partecipante di test ─────────────────────────────
    double_scan_time = now - timedelta(minutes=30)
    db.collection("entrance_scans").document(event_id).collection("scans").document(PRE_SCANNED_MEMBER_ID).set({
        "scanned_at": double_scan_time,
        "scan_token": token,
    })
    _print(f"Membro '{PRE_SCANNED_MEMBER_ID}' pre-scansionato 30 min fa", "✓")

    # ── Riepilogo ─────────────────────────────────────────────────────────────
    scan_url = f"http://localhost:3000/scan/{token}"

    print("\n" + "─" * 60)
    print("  RIEPILOGO SCENARIO DI TEST")
    print("─" * 60)
    print(f"  Evento ID  : {event_id}")
    print(f"  Scan Token : {token}")
    print(f"  Scan URL   : {scan_url}")
    print(f"  Base email : {BASE_TEST_EMAIL}")
    print()
    print("  TESSERE DA SCANSIONARE:")
    print(f"  KmSbPtCkafBLaoF9zGr4  → atteso: ✅ VALID (prima scan)")
    print(f"  HIWVbeT2RfjSv9jZGY9y  → atteso: ✅ VALID (prima scan)")
    print(f"  Aq7MxK2pLd9VrT6HnCb1  → atteso: ✅ VALID (prima scan)")
    print(f"  Ir6QyT9vHb3WpE7LmKd1  → atteso: ❌ EVENTO NON ACQUISTATO")
    print(f"  {PRE_SCANNED_MEMBER_ID}   → atteso: 🟡 GIÀ REGISTRATO")
    print(f"  (tessera inesistente)  → atteso: ❌ TESSERA NON RICONOSCIUTA")
    print()
    print(f"  Totale membri seedati       : {len(all_members)}")
    print(f"  Membri con ticket evento    : {len(participants_to_add)}")
    print(f"  Membri senza ticket evento  : {len(NON_ATTENDING_MEMBERS)}")
    print(f"  Membri con wallet associato : {len(all_members) - len(missing_pass_data)}")
    print("─" * 60)
    print()
    print("  Per testare:")
    print(f"  1. Apri il link sul telefono: {scan_url}")
    print(f"  2. Scansiona i QR delle tessere nelle immagini di test")
    print()

    return event_id, token


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed entrance test data into Firestore emulator")
    parser.add_argument("--reset", action="store_true", help="Delete previously seeded documents before re-seeding")
    parser.add_argument("--event-id", default=None, help="Existing event ID to reset (required with --reset if no prior seed)")
    parser.add_argument("--token", default=None, help="Existing token to delete (used with --reset)")
    parser.add_argument(
        "--pass-csv",
        default=None,
        help=(
            "Path to Pass_Data.csv. If omitted, uses ENTRANCE_PASS_CSV or "
            "~/Downloads/Pass_Data.csv when available."
        ),
    )
    args = parser.parse_args()

    emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST", "")
    print(f"\n🔌  Firestore target: {emulator_host or '(production — be careful!)'}")
    if "production" in emulator_host or not emulator_host:
        confirm = input("  ⚠️  Stai scrivendo su Firestore REALE. Continui? [y/N] ").strip().lower()
        if confirm != "y":
            print("  Annullato.")
            sys.exit(0)

    if args.reset and args.event_id:
        reset(args.event_id, args.token or "")

    pass_csv_path = _resolve_pass_csv_path(args.pass_csv)
    pass_lookup = _load_pass_lookup(pass_csv_path)
    missing_ids = [mid for mid in ALL_MEMBER_IDS if mid not in pass_lookup]
    if missing_ids:
        raise RuntimeError(
            "Pass data missing for seeded membership IDs: "
            + ", ".join(missing_ids)
        )

    _print(f"Pass CSV caricato: {pass_csv_path}", "✓")
    _print(f"Mapping wallet trovati: {len(pass_lookup)}", "✓")
    seed(pass_lookup)


if __name__ == "__main__":
    main()
