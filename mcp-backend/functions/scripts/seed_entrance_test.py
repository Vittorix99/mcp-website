#!/usr/bin/env python3
"""
Entrance Scanner — Test Data Seed
==================================

Popola il Firestore emulator con tutti i dati necessari per testare
la logica di ingresso con le tessere reali di Vittorio Di Giorgio.

Scenari coperti
---------------
  1. KmSbPtCkafBLaoF9zGr4  → membership valida + partecipante  → "valid" al primo scan
  2. HIWVbeT2RfjSv9jZGY9y  → membership valida + partecipante  → "valid" al primo scan
  3. membro_no_purchase     → membership valida, NESSUN biglietto → "invalid_no_purchase"
  4. membro_double_scan     → membership valida + partecipante + già scansionato → "already_scanned"
  5. (tessera inesistente)  → nessun documento → "invalid_member_not_found" (testa lato scanner)

PRE-REQUISITO
  firebase emulators:start --only firestore
  oppure
  export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080

USO
  cd mcp-backend/functions
  python scripts/seed_entrance_test.py [--reset]

  --reset   elimina tutti i documenti creati da questo script prima di riseedare
"""

import argparse
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone

# ── Punta sull'emulator se l'env non è già impostato ──────────────────────────
if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"

import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

# ── Init Firebase Admin (usa app default se già inizializzata) ─────────────────
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.ApplicationDefault())

db = admin_firestore.client()

# ─────────────────────────────────────────────────────────────────────────────
# Dati fissi
# ─────────────────────────────────────────────────────────────────────────────

# Tessere reali di Vittorio Di Giorgio (dagli screenshot)
REAL_MEMBER_IDS = {
    "KmSbPtCkafBLaoF9zGr4": {
        "name": "Vittorio",
        "surname": "Di Giorgio",
        "email": "highdreams290@gmail.com",
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
        "email": "vittorio.digiorgio@hotmail.it",
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
EXTRA_MEMBERS = {
    "test_no_purchase_001": {
        "name": "Mario",
        "surname": "Rossi",
        "email": "mario.rossi@test.it",
        "phone": "+393500000001",
        "birthdate": "15-06-1995",
        "subscription_valid": True,
        "end_date": "01-01-2027",
        "start_date": "01-01-2026",
        "membership_sent": False,
        "membership_type": "standard",
    },
    "test_double_scan_002": {
        "name": "Luca",
        "surname": "Bianchi",
        "email": "luca.bianchi@test.it",
        "phone": "+393500000002",
        "birthdate": "20-03-1993",
        "subscription_valid": True,
        "end_date": "01-01-2027",
        "start_date": "01-01-2026",
        "membership_sent": False,
        "membership_type": "standard",
    },
}

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

def seed():
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
    for mid, data in all_members.items():
        db.collection("memberships").document(mid).set(data)
    _print(f"{len(all_members)} membri scritti in Firestore", "✓")

    # ── 5. Partecipanti ───────────────────────────────────────────────────────
    # Scenari 1, 2, 4 (i due reali + double_scan) hanno biglietto
    participants_to_add = [
        *[(mid, data) for mid, data in REAL_MEMBER_IDS.items()],
        ("test_double_scan_002", EXTRA_MEMBERS["test_double_scan_002"]),
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

    # ── 5. Pre-scansiona test_double_scan_002 ─────────────────────────────────
    double_scan_time = now - timedelta(minutes=30)
    db.collection("entrance_scans").document(event_id).collection("scans").document("test_double_scan_002").set({
        "scanned_at": double_scan_time,
        "scan_token": token,
    })
    _print("Membro 'double_scan_002' pre-scansionato 30 min fa", "✓")

    # ── Riepilogo ─────────────────────────────────────────────────────────────
    scan_url = f"http://localhost:3000/scan/{token}"

    print("\n" + "─" * 60)
    print("  RIEPILOGO SCENARIO DI TEST")
    print("─" * 60)
    print(f"  Evento ID  : {event_id}")
    print(f"  Scan Token : {token}")
    print(f"  Scan URL   : {scan_url}")
    print()
    print("  TESSERE DA SCANSIONARE:")
    print(f"  KmSbPtCkafBLaoF9zGr4  → atteso: ✅ VALID (prima scan)")
    print(f"  HIWVbeT2RfjSv9jZGY9y  → atteso: ✅ VALID (prima scan)")
    print(f"  test_no_purchase_001   → atteso: ❌ EVENTO NON ACQUISTATO")
    print(f"  test_double_scan_002   → atteso: 🟡 GIÀ REGISTRATO")
    print(f"  (tessera inesistente)  → atteso: ❌ TESSERA NON RICONOSCIUTA")
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

    seed()


if __name__ == "__main__":
    main()
