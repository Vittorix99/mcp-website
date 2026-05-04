"""
Conftest per i test di integrazione dell'Entrance Scanner.

IMPORTANTE — questi test girano SOLO contro il Firestore emulator.
Se l'emulatore non è attivo o non è configurabile prima dell'inizializzazione
Firebase, l'intera suite viene saltata automaticamente.

Tutto il dato di test (evento, membership, partecipanti, scan token) viene
creato UNA SOLA VOLTA in `entrance_seed` (scope="session") prima che parta
qualsiasi test, e rimosso al teardown della sessione.
"""

import os
import socket
from dataclasses import dataclass
from typing import List
from uuid import uuid4

import pytest


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _configure_firestore_emulator_before_firebase_import() -> None:
    """
    Imposta FIRESTORE_EMULATOR_HOST prima di importare firebase_config.
    Se lo facciamo dopo, il client Firestore viene già creato contro cloud.
    """
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        return

    configured_port = os.environ.get("FIRESTORE_EMULATOR_PORT")
    candidate_ports = [configured_port] if configured_port else []
    candidate_ports.extend(["8085", "8080"])

    for raw_port in candidate_ports:
        if not raw_port:
            continue
        port = int(raw_port)
        for host in ("127.0.0.1", "localhost"):
            if _is_port_open(host, port):
                os.environ["FIRESTORE_EMULATOR_HOST"] = f"{host}:{port}"
                return


_configure_firestore_emulator_before_firebase_import()

from config.firebase_config import db
from dto.entrance_api import GenerateScanTokenRequestDTO
from dto.event_api import CreateEventRequestDTO
from models import EventParticipant, Membership, PaymentMethod
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from services.entrance_service import EntranceService
from services.events.events_service import EventsService


# ---------------------------------------------------------------------------
# Guard: salta tutto se il Firestore emulator non è raggiungibile
# ---------------------------------------------------------------------------

def _require_emulator() -> None:
    """
    Verifica che FIRESTORE_EMULATOR_HOST sia impostato e raggiungibile.
    Chiama pytest.skip() se l'emulatore non è disponibile, così nessun test
    in questa suite tocca accidentalmente il database cloud.
    """
    host = os.environ.get("FIRESTORE_EMULATOR_HOST", "")
    if not host:
        pytest.skip("Firestore emulator non attivo — FIRESTORE_EMULATOR_HOST non impostato")

    host_name, raw_port = host.rsplit(":", 1)
    if not _is_port_open(host_name, int(raw_port)):
        pytest.skip(f"Firestore emulator non raggiungibile su {host}")


@pytest.fixture(scope="session", autouse=True)
def _emulator_guard():
    """Fixture autouse: blocca l'intera suite se l'emulatore non è attivo."""
    _require_emulator()


# ---------------------------------------------------------------------------
# Struttura dati del seed
# ---------------------------------------------------------------------------

@dataclass
class MemberSeed:
    membership_id: str
    name: str
    surname: str


@dataclass
class EntranceSeed:
    """Tutti gli ID pre-seeded disponibili per i test."""
    event_id: str
    scan_token: str
    scan_url: str

    # Membri validi registrati come partecipanti all'evento (step 3+4)
    valid_members: List[MemberSeed]

    # Membro con membership valida ma NESSUN biglietto per l'evento (step 6)
    member_no_purchase: MemberSeed

    # Membro con membership NON VALIDA (subscription_valid=False) (step 8)
    member_invalid_subscription: MemberSeed

    # Membro dedicato al test "already_scanned" (step 7)
    # È registrato come partecipante ma NON ancora scansionato all'inizio
    member_for_double_scan: MemberSeed

    # Membro dedicato ai test di manual_entry — ha biglietto, mai scansionato
    member_for_manual_entry: MemberSeed


# ---------------------------------------------------------------------------
# Fixture di seed — scope="session", creazione unica prima di tutti i test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def entrance_seed():
    """
    Crea tutti i dati di test nel Firestore emulator UNA SOLA VOLTA.

    Struttura creata:
      events/{event_id}
      scan_tokens/{token}
      memberships/{id}  × 5  (3 validi+partecipanti, 1 senza biglietto,
                               1 subscription_valid=False, 1 per double-scan)
      participants/{event_id}/participants_event/{id}  × 4
        (i 3 validi + il membro per double-scan)

    Tutto viene eliminato in teardown.
    """
    events_service = EventsService()
    membership_repo = MembershipRepository()
    participant_repo = ParticipantRepository()
    entrance_service = EntranceService()

    created_membership_ids: List[str] = []
    created_participants: List[tuple] = []      # (event_id, participant_id)
    entrance_scans_to_delete: List[tuple] = []  # (event_id, membership_id)
    event_id = None
    token = None

    try:
        # ── 1. Crea evento ──────────────────────────────────────────────────
        from datetime import datetime, timedelta, timezone
        date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
        dto = CreateEventRequestDTO.model_validate({
            "title": f"Entrance Integration Test {uuid4().hex[:8]}",
            "date": date_value,
            "startTime": "21:00",
            "endTime": "23:00",
            "location": "Test Venue",
            "locationHint": "Ingresso principale",
            "price": 10.0,
            "status": "active",
        })
        result = events_service.create_event(dto, admin_uid="admin-test")
        event_id = result.event_id

        # ── 2. Crea scan token ──────────────────────────────────────────────
        token_result = entrance_service.generate_scan_token(
            GenerateScanTokenRequestDTO(event_id=event_id),
            admin_uid="admin-test",
        )
        token = token_result.token
        scan_url = token_result.scan_url

        # ── 3. Crea membership ──────────────────────────────────────────────

        def _make_membership(name, surname, subscription_valid=True) -> MemberSeed:
            suffix = uuid4().hex[:8]
            m = Membership(
                name=name,
                surname=surname,
                email=f"entrance.test.{suffix}@example.com",
                phone=f"+39{str(uuid4().int)[-10:]}",
                birthdate="01-01-1990",
                subscription_valid=subscription_valid,
            )
            mid = membership_repo.create_from_model(m)
            created_membership_ids.append(mid)
            return MemberSeed(membership_id=mid, name=name, surname=surname)

        def _add_participant(member: MemberSeed) -> None:
            p = EventParticipant(
                event_id=event_id,
                name=member.name,
                surname=member.surname,
                email=f"participant.{uuid4().hex[:8]}@example.com",
                phone=f"+39{str(uuid4().int)[-10:]}",
                birthdate="01-01-1990",
                membership_id=member.membership_id,
                membership_included=True,
                ticket_sent=False,
                location_sent=False,
                newsletter_consent=False,
                price=10.0,
                payment_method=PaymentMethod.CASH,
            )
            pid = participant_repo.create_from_model(event_id, p)
            created_participants.append((event_id, pid))

        # 3 membri validi + partecipanti (step 3+4)
        valid_members = [
            _make_membership("Alice", "Bianchi"),
            _make_membership("Bob", "Verdi"),
            _make_membership("Carlo", "Neri"),
        ]
        for member in valid_members:
            _add_participant(member)
            entrance_scans_to_delete.append((event_id, member.membership_id))

        # Membro per test "already_scanned" (step 7) — ha biglietto, scansionato nel test
        member_for_double_scan = _make_membership("Già", "Entrato")
        _add_participant(member_for_double_scan)
        entrance_scans_to_delete.append((event_id, member_for_double_scan.membership_id))

        # Membro per test manual_entry — ha biglietto, mai scansionato all'inizio
        member_for_manual_entry = _make_membership("Manuale", "Ingresso")
        _add_participant(member_for_manual_entry)
        entrance_scans_to_delete.append((event_id, member_for_manual_entry.membership_id))

        # Membro senza biglietto (step 6)
        member_no_purchase = _make_membership("Senza", "Biglietto")

        # Membro con membership non valida (step 8)
        member_invalid_subscription = _make_membership(
            "Scaduto", "Tesserato", subscription_valid=False
        )

        yield EntranceSeed(
            event_id=event_id,
            scan_token=token,
            scan_url=scan_url,
            valid_members=valid_members,
            member_no_purchase=member_no_purchase,
            member_invalid_subscription=member_invalid_subscription,
            member_for_double_scan=member_for_double_scan,
            member_for_manual_entry=member_for_manual_entry,
        )

    finally:
        # ── Teardown ────────────────────────────────────────────────────────
        for ev_id, mid in entrance_scans_to_delete:
            try:
                db.collection("entrance_scans").document(ev_id)\
                  .collection("scans").document(mid).delete()
            except Exception:
                pass

        for ev_id, pid in created_participants:
            try:
                ParticipantRepository().delete(ev_id, pid)
            except Exception:
                pass

        for mid in created_membership_ids:
            try:
                MembershipRepository().delete(mid)
            except Exception:
                pass

        if token:
            try:
                db.collection("scan_tokens").document(token).delete()
            except Exception:
                pass

        if event_id:
            try:
                EventsService().delete_event(event_id, admin_uid="admin-test")
            except Exception:
                pass


@pytest.fixture(scope="session")
def entrance_service():
    return EntranceService()
