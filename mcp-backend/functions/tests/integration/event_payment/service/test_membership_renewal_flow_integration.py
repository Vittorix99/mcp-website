"""
Integration test — flusso completo di rinnovo tessera.

Scenario:
  1. Un utente è membro dall'anno precedente (start_date nel 2025).
  2. Acquista la partecipazione a un evento ONLY_MEMBERS nel 2026.
  3. Il sistema lo riconosce come non-membro dell'anno corrente →
     finisce in membership_targets → durante il capture la membership
     viene rinnovata (nuove date, send_card_on_create=True).
  4. Si chiama send_card() → viene creato un wallet pass (Pass2U mockato)
     e inviata una VERA email via MailerSend a mcpweb.test+rinnovo@gmail.com.
  5. Firestore riflette il rinnovo: start_date 2026, membership_sent=True.

Run:
    pytest tests/integration/event_payment/service/test_membership_renewal_flow_integration.py -v -s
"""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from dto import CheckoutParticipantDTO, EventDTO, OrderCaptureDTO
from models import (
    EventOrder,
    EventPurchaseAccessType,
    Membership,
    MembershipPassResult,
    PurchaseTypes,
)
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.order_repository import OrderRepository
from services.events.events_service import EventsService
from services.memberships.memberships_service import MembershipsService
from services.payments.event_payment_service import EventPaymentService

# ---------------------------------------------------------------------------
# Costanti del test
# ---------------------------------------------------------------------------

_TEST_EMAIL = "mcpweb.test+rinnovo@gmail.com"
_FAKE_PASS_ID = "integ-renewal-pass-001"
_FAKE_WALLET_URL = "https://bpwallet.io/pass/integ-renewal-test"
_MODEL_ID = "integ-test-model-renewal"


# ---------------------------------------------------------------------------
# Fixtures locali
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _seed_wallet_model(db=None):
    """Seed del modello Pass2U nel Firestore emulator."""
    from config.firebase_config import db as firestore_db
    ref = firestore_db.collection("membership_settings").document("current_model")
    ref.set({"model_id": _MODEL_ID})
    yield
    ref.delete()


@pytest.fixture
def membership_repository():
    return MembershipRepository()


@pytest.fixture
def membership_settings_repository():
    return MembershipSettingsRepository()


@pytest.fixture
def order_repository():
    return OrderRepository()


@pytest.fixture
def memberships_service():
    return MembershipsService()


@pytest.fixture
def events_service():
    return EventsService()


@pytest.fixture
def ensure_membership_fee(membership_settings_repository):
    """Garantisce che la quota associativa per l'anno corrente sia impostata."""
    from config.firebase_config import db as firestore_db
    from google.cloud import firestore

    year = str(datetime.now(timezone.utc).year)
    previous = membership_settings_repository.get_price_by_year(year)
    membership_settings_repository.set_price_by_year(year, 20.0)
    yield 20.0
    doc_ref = firestore_db.collection("membership_settings").document("price")
    if previous is None:
        doc_ref.update({f"price_by_year.{year}": firestore.DELETE_FIELD})
    else:
        doc_ref.update({f"price_by_year.{year}": previous})


@pytest.fixture
def previous_year_membership(membership_repository):
    """Inserisce nel Firestore emulator un membro dell'anno precedente."""
    prev_year = datetime.now(timezone.utc).year - 1
    suffix = uuid4().hex[:6]
    membership = Membership(
        name="Mario",
        surname="Rossi",
        email=_TEST_EMAIL,
        phone=f"+39333{suffix}",
        birthdate="01-01-1990",
        start_date=f"{prev_year}-09-05T22:55:43Z",
        end_date=f"31-12-{prev_year}",
        subscription_valid=True,
        membership_sent=True,
        send_card_on_create=False,
        membership_type="event",
        wallet_pass_id="old-pass-id",
        wallet_url="https://bpwallet.io/pass/old-pass",
    )
    membership_id = membership_repository.create_from_model(membership)
    yield membership_id
    try:
        membership_repository.delete(membership_id)
    except Exception:
        pass


@pytest.fixture
def only_members_event(events_service):
    """Crea un evento ONLY_MEMBERS nel Firestore emulator."""
    created = []
    date_value = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y")
    dto = EventDTO.from_payload({
        "title": f"Rinnovo Test Event {uuid4().hex[:6]}",
        "date": date_value,
        "startTime": "21:00",
        "endTime": "23:00",
        "location": "Integration Hall",
        "locationHint": "Ingresso principale",
        "price": 12.0,
        "fee": 0.0,
        "status": "active",
        "purchaseMode": EventPurchaseAccessType.ONLY_MEMBERS.value,
    })
    result = events_service.create_event(dto, admin_uid="admin-test")
    event_id = result.get("eventId")
    created.append(event_id)
    yield event_id
    for eid in created:
        if eid:
            try:
                events_service.delete_event(eid, admin_uid="admin-test")
            except Exception:
                pass


def _participant() -> CheckoutParticipantDTO:
    return CheckoutParticipantDTO(
        name="Mario",
        surname="Rossi",
        email=_TEST_EMAIL,
        phone="+393330000001",
        birthdate="01-01-1990",
    )


def _paypal_capture_payload(event_id: str) -> dict:
    curr_year = datetime.now(timezone.utc).year
    return {
        "id": "order-renewal-integ",
        "status": "COMPLETED",
        "payment_source": {
            "paypal": {
                "name": {"given_name": "Mario", "surname": "Rossi"},
                "email_address": _TEST_EMAIL,
            }
        },
        "purchase_units": [
            {
                "reference_id": event_id,
                "payments": {
                    "captures": [
                        {
                            "id": "CAP-RENEWAL-INTEG",
                            "status": "COMPLETED",
                            "final_capture": True,
                            "amount": {"value": "32.00", "currency_code": "EUR"},
                            "create_time": f"{curr_year}-03-19T10:00:00Z",
                            "seller_receivable_breakdown": {
                                "paypal_fee": {"value": "1.0"},
                                "net_amount": {"value": "31.0"},
                            },
                        }
                    ]
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# Test principale
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.email
def test_renewal_flow_end_to_end_with_email(
    only_members_event,
    previous_year_membership,
    membership_repository,
    order_repository,
):
    """
    Flusso completo:
      - Membro anno precedente acquista evento ONLY_MEMBERS
      - Durante il capture: tessera rinnovata (start_date aggiornata) + pass creato + email inviata
      - Una vera email con la tessera arriva a mcpweb.test+rinnovo@gmail.com
      - Dopo il capture: membership_sent=True e wallet_url valorizzato (senza chiamate extra)
    """
    event_id = only_members_event
    membership_id = previous_year_membership
    curr_year = datetime.now(timezone.utc).year

    # ------------------------------------------------------------------
    # Step 1: verifica stato iniziale — la membership è dell'anno scorso
    # ------------------------------------------------------------------
    initial = membership_repository.get(membership_id)
    assert initial is not None
    initial_start = datetime.fromisoformat(initial.start_date.replace("Z", "+00:00"))
    assert initial_start.year < curr_year, "Prerequisito: la membership deve essere dell'anno precedente"
    print(f"\n[STEP 1] Membership esistente: {membership_id} — start_date: {initial.start_date}")

    # ------------------------------------------------------------------
    # Step 2: costruisci l'ordine staged come farebbe create_order_event
    #   Il partecipante è in membership_targets perché è un membro scaduto
    # ------------------------------------------------------------------
    participant_payload = _participant().to_payload()
    order_id = f"order-renewal-integ-{uuid4().hex[:8]}"
    event_order = EventOrder(
        order_id=order_id,
        order_status="CREATED",
        purchase_type=PurchaseTypes.EVENT,
        cart=[{"eventId": event_id}],
        total=32.0,
        reference_id=event_id,
        event_meta={},
        event_id=event_id,
        participants=[participant_payload],
        event_price=12.0,
        event_fee=0.0,
        membership_targets=[participant_payload],   # ← membro scaduto = target rinnovo
        membership_fee=20.0,
        purchase_mode=EventPurchaseAccessType.ONLY_MEMBERS,
        membership_lookup={},                       # ← nessun membro valido dell'anno corrente
    )
    order_repository.save(order_id, event_order)
    print(f"[STEP 2] Ordine staged salvato: {order_id}")

    # ------------------------------------------------------------------
    # Step 3: cattura ordine (PayPal mockato, Pass2U mockato, MailerSend reale)
    #   capture_order_event chiama ora send_card() internamente per il membro rinnovato
    # ------------------------------------------------------------------
    service = EventPaymentService()
    capture_data = _paypal_capture_payload(event_id)

    mock_wallet = MembershipPassResult(
        pass_id=_FAKE_PASS_ID,
        wallet_url=_FAKE_WALLET_URL,
        apple_wallet_url=_FAKE_WALLET_URL,
        google_wallet_url=_FAKE_WALLET_URL,
    )

    with patch.object(service, "capture_paypal_order", return_value=capture_data), \
         patch("services.payments.event_payment_service.ApiHelper.json_serialize",
               side_effect=lambda body: json.dumps(body)), \
         patch("services.memberships.pass2u_service.Pass2UService") as mock_p2u:

        mock_p2u.return_value.create_membership_pass.return_value = mock_wallet
        mock_p2u.return_value.invalidate_membership_pass.return_value = True
        result = service.capture_order_event(OrderCaptureDTO(order_id=order_id))

    print(f"[STEP 3] Capture completata: purchase_id={result.get('purchase_id')}")
    assert result.get("purchase_id"), "Il capture deve restituire un purchase_id"

    # ------------------------------------------------------------------
    # Step 4: verifica rinnovo + invio tessera su Firestore
    #   membership_sent deve essere già True: send_card è chiamata dentro capture
    # ------------------------------------------------------------------
    final = membership_repository.get(membership_id)
    assert final is not None

    final_start = datetime.fromisoformat(final.start_date.replace("Z", "+00:00"))
    assert final_start.year == curr_year, (
        f"start_date deve essere nel {curr_year}, trovato: {final.start_date}"
    )
    assert str(curr_year) in final.end_date, (
        f"end_date deve contenere {curr_year}, trovato: {final.end_date}"
    )
    assert final.subscription_valid is True
    assert final.membership_sent is True, "membership_sent deve essere True dopo il capture"
    assert final.wallet_url == _FAKE_WALLET_URL, (
        f"wallet_url deve essere {_FAKE_WALLET_URL}, trovato: {final.wallet_url}"
    )

    print(f"[STEP 4] Rinnovo e invio verificati — start_date: {final.start_date}, membership_sent=True")
    print(f"\n✓ Controlla la casella: {_TEST_EMAIL}")
    print(f"  Oggetto: 'La tua tessera MCP'")
    print(f"  Wallet URL (mock): {_FAKE_WALLET_URL}\n")
