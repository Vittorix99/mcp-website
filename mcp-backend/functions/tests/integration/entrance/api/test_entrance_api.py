"""
Integration tests — Entrance Scanner API layer
===============================================

Testano il livello HTTP dei tre endpoint di entrance_api.py,
chiamando le Cloud Functions direttamente con DummyRequest e
verificando status code e shape della risposta.

La logica di business è già coperta da test_entrance_service.py;
qui si verifica che:
  - i decorator di validazione restituiscano i codici corretti (400/401)
  - l'autenticazione admin sia obbligatoria dove richiesto
  - la response shape sia consistente con il contratto API
  - i casi "safe" (idempotenti) producano i risultati attesi end-to-end

PRE-REQUISITO: Firestore emulator attivo su porta 8080.
  firebase emulators:start --only firestore
"""

import pytest

from api import entrance as entrance_api
from config.firebase_config import db
from tests.utils import DummyRequest, unwrap_response


# ---------------------------------------------------------------------------
# POST /entrance_generate_scan_token
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_generate_scan_token_success(entrance_seed):
    """
    POST con event_id valido e header admin → 201 con token (32 char) e scan_url.
    Il token creato viene eliminato nel finally per non inquinare il seed.
    """
    req = DummyRequest(
        method="POST",
        json={"event_id": entrance_seed.event_id},
    )
    resp, status = unwrap_response(entrance_api.entrance_generate_scan_token(req))

    token = resp.get("token") if isinstance(resp, dict) else None
    try:
        assert status == 201, f"Atteso 201, ottenuto {status}: {resp}"
        assert token, "Il campo 'token' non deve essere vuoto"
        assert len(token) == 32, f"Attesi 32 char hex, ottenuto {len(token)}"
        assert resp.get("scan_url") == f"https://musiconnectingpeople.com/scan/{token}"
    finally:
        if token:
            try:
                db.collection("scan_tokens").document(token).delete()
            except Exception:
                pass


@pytest.mark.integration
def test_generate_scan_token_requires_admin_auth():
    """
    POST senza Authorization header → 401 (intercettato da @require_admin
    prima ancora di leggere il body).

    Nota: DummyRequest(headers={}) non funziona — {} è falsy, quindi il
    costruttore applica comunque il default {"Authorization": "Bearer test-token"}.
    La soluzione è creare il request con default e poi azzerare headers.
    """
    req = DummyRequest(method="POST", json={"event_id": "any"})
    req.headers = {}  # override esplicito dopo la costruzione
    _, status = unwrap_response(entrance_api.entrance_generate_scan_token(req))
    assert status == 401


@pytest.mark.integration
def test_generate_scan_token_missing_event_id():
    """POST con body vuoto → 400 da @validate_body_fields."""
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(entrance_api.entrance_generate_scan_token(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_generate_scan_token_missing_body():
    """POST senza JSON body → 400 da @require_json_body."""
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(entrance_api.entrance_generate_scan_token(req))
    assert status == 400


@pytest.mark.integration
def test_generate_scan_token_event_not_found():
    """POST con event_id inesistente → 404 da NotFoundError nel service."""
    req = DummyRequest(
        method="POST",
        json={"event_id": "evento-che-non-esiste-0000"},
    )
    resp, status = unwrap_response(entrance_api.entrance_generate_scan_token(req))
    assert status == 404


@pytest.mark.integration
def test_generate_scan_token_wrong_method():
    """GET su endpoint POST → 405."""
    req = DummyRequest(method="GET", json={"event_id": "any"})
    resp, status = unwrap_response(entrance_api.entrance_generate_scan_token(req))
    assert status == 405


# ---------------------------------------------------------------------------
# GET /entrance_verify_scan_token
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_verify_scan_token_valid(entrance_seed):
    """
    GET con token valido → 200, valid=True, event_id e event_title valorizzati.
    """
    req = DummyRequest(
        method="GET",
        args={"token": entrance_seed.scan_token},
    )
    resp, status = unwrap_response(entrance_api.entrance_verify_scan_token(req))

    assert status == 200, f"Atteso 200, ottenuto {status}: {resp}"
    assert resp.get("valid") is True
    assert resp.get("event_id") == entrance_seed.event_id
    assert resp.get("event_title"), "event_title non deve essere vuoto"


@pytest.mark.integration
def test_verify_scan_token_not_found():
    """GET con token inesistente → 401, valid=False, reason='not_found'."""
    req = DummyRequest(
        method="GET",
        args={"token": "0000000000000000000000000000ffff"},
    )
    resp, status = unwrap_response(entrance_api.entrance_verify_scan_token(req))

    assert status == 401, f"Atteso 401, ottenuto {status}"
    assert resp.get("valid") is False
    assert resp.get("reason") == "not_found"


@pytest.mark.integration
def test_verify_scan_token_missing_param():
    """GET senza query param 'token' → 400 da @validate_query_params."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(entrance_api.entrance_verify_scan_token(req))
    assert status == 400


@pytest.mark.integration
def test_verify_scan_token_wrong_method():
    """POST su endpoint GET → 405."""
    req = DummyRequest(method="POST", args={"token": "any"})
    resp, status = unwrap_response(entrance_api.entrance_verify_scan_token(req))
    assert status == 405


# ---------------------------------------------------------------------------
# POST /entrance_validate
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_validate_entry_invalid_token(entrance_seed):
    """
    POST con token inesistente → 200 con result='invalid_token'.
    Usa un membership_id reale ma token falso.
    """
    req = DummyRequest(
        method="POST",
        json={
            "membership_id": entrance_seed.valid_members[0].membership_id,
            "scan_token": "0000000000000000000000000000ffff",
        },
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))

    assert status == 200
    assert resp.get("result") == "invalid_token"


@pytest.mark.integration
def test_validate_entry_no_purchase(entrance_seed):
    """
    POST membro valido ma senza biglietto → 200 con result='invalid_no_purchase'.
    Idempotente: non scrive dati, sicuro da chiamare più volte.
    """
    member = entrance_seed.member_no_purchase
    req = DummyRequest(
        method="POST",
        json={
            "membership_id": member.membership_id,
            "scan_token": entrance_seed.scan_token,
        },
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))

    assert status == 200
    assert resp.get("result") == "invalid_no_purchase"


@pytest.mark.integration
def test_validate_entry_invalid_subscription(entrance_seed):
    """
    POST membro con subscription_valid=False e nessun biglietto
    → 200 con result='invalid_no_purchase'.
    """
    member = entrance_seed.member_invalid_subscription
    req = DummyRequest(
        method="POST",
        json={
            "membership_id": member.membership_id,
            "scan_token": entrance_seed.scan_token,
        },
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))

    assert status == 200
    assert resp.get("result") == "invalid_no_purchase"


@pytest.mark.integration
def test_validate_entry_response_shape(entrance_seed):
    """
    La risposta deve contenere sempre i campi result, membership, scanned_at
    indipendentemente dall'esito — contratto API stabile.
    """
    req = DummyRequest(
        method="POST",
        json={
            "membership_id": entrance_seed.member_no_purchase.membership_id,
            "scan_token": entrance_seed.scan_token,
        },
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))

    assert status == 200
    assert "result" in resp, "Campo 'result' mancante nella risposta"
    assert "membership" in resp, "Campo 'membership' mancante nella risposta"
    assert "scanned_at" in resp, "Campo 'scanned_at' mancante nella risposta"


@pytest.mark.integration
def test_validate_entry_missing_scan_token():
    """POST con solo membership_id → 400 da @validate_body_fields."""
    req = DummyRequest(
        method="POST",
        json={"membership_id": "some-id"},
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_validate_entry_missing_membership_id():
    """POST con solo scan_token → 400 da @validate_body_fields."""
    req = DummyRequest(
        method="POST",
        json={"scan_token": "some-token"},
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_validate_entry_missing_body():
    """POST senza JSON body → 400 da @require_json_body."""
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(entrance_api.entrance_validate(req))
    assert status == 400


@pytest.mark.integration
def test_validate_entry_wrong_method(entrance_seed):
    """GET su endpoint POST → 405."""
    req = DummyRequest(
        method="GET",
        json={
            "membership_id": "any",
            "scan_token": entrance_seed.scan_token,
        },
    )
    resp, status = unwrap_response(entrance_api.entrance_validate(req))
    assert status == 405
