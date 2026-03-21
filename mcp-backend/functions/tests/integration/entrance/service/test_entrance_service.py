"""
Integration tests — Entrance Scanner
=====================================

PRE-REQUISITO: Firestore emulator attivo su porta 8080.
  firebase emulators:start --only firestore

Se l'emulatore non è raggiungibile l'intera suite viene saltata
automaticamente (nessun dato viene mai scritto in produzione).

Tutti i dati (evento, membership, partecipanti, token) sono creati
una volta sola dalla fixture `entrance_seed` (scope="session") nel
conftest.py — i test leggono gli ID pre-seeded e non creano nulla.

Scenari coperti
---------------
  1. Creazione evento                                → ID evento valido
  2. Generazione scan token e URL                   → token 32 char, URL corretto
  3+4. Creazione 3 membership + 3 partecipanti      → (nel seed)
  5. Scansione tessere valide                        → result "valid"
  6. Membro senza biglietto per l'evento             → result "invalid_no_purchase"
  7. Membro già entrato — seconda scansione          → result "already_scanned"
  8. Membro con subscription_valid=False             → result "invalid_no_purchase"
  Extra. Token inesistente                           → result "invalid_token" / valid=False
"""

import pytest


# ---------------------------------------------------------------------------
# Step 1 — Evento creato correttamente
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_event_was_created(entrance_seed):
    """Step 1: Il seed ha creato un evento con ID non nullo."""
    assert entrance_seed.event_id, "event_id deve essere valorizzato"


# ---------------------------------------------------------------------------
# Step 2 — Scan token e URL
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_scan_token_format(entrance_seed):
    """
    Step 2: Il token ha 32 caratteri hex (secrets.token_hex(16)) e l'URL
    contiene esattamente il token.
    """
    token = entrance_seed.scan_token
    assert token, "Il token non deve essere vuoto"
    assert len(token) == 32, f"Attesi 32 caratteri hex, ottenuto: {len(token)}"
    assert entrance_seed.scan_url == f"https://musiconnectingpeople.com/scan/{token}"


@pytest.mark.integration
def test_verify_scan_token_valid(entrance_seed, entrance_service):
    """
    Step 2: verify_scan_token su un token attivo ritorna valid=True con
    event_id e titolo dell'evento valorizzati.
    """
    result = entrance_service.verify_scan_token(entrance_seed.scan_token)

    assert result["valid"] is True
    assert result["event_id"] == entrance_seed.event_id
    assert result["event_title"], "Il titolo dell'evento non deve essere vuoto"


# ---------------------------------------------------------------------------
# Step 5 — Scansione delle tessere valide (3 membri + partecipanti già nel seed)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_valid_members_all_enter(entrance_seed, entrance_service):
    """
    Step 3+4+5: I 3 membri con membership valida e biglietto acquistato
    vengono scansionati — tutti devono risultare "valid" con nome e cognome
    corretti.
    """
    for member in entrance_seed.valid_members:
        result = entrance_service.validate_entry(
            member.membership_id, entrance_seed.scan_token
        )
        assert result["result"] == "valid", (
            f"Atteso 'valid' per {member.name} {member.surname}, "
            f"ottenuto: {result['result']}"
        )
        assert result["membership"]["name"] == member.name
        assert result["membership"]["surname"] == member.surname
        assert result["scanned_at"] is None, (
            "scanned_at deve essere None al primo ingresso valido"
        )


# ---------------------------------------------------------------------------
# Step 6 — Membro con membership ma senza biglietto → rifiutato
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_member_without_purchase_rejected(entrance_seed, entrance_service):
    """
    Step 6: Il membro ha una membership valida ma non ha acquistato il biglietto
    per questo evento. Nessun record in participants_event → "invalid_no_purchase".
    """
    member = entrance_seed.member_no_purchase
    result = entrance_service.validate_entry(
        member.membership_id, entrance_seed.scan_token
    )
    assert result["result"] == "invalid_no_purchase", (
        f"Atteso 'invalid_no_purchase', ottenuto: {result['result']}"
    )


# ---------------------------------------------------------------------------
# Step 7 — Membro già entrato → bloccato alla seconda scansione
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_already_scanned_member_blocked(entrance_seed, entrance_service):
    """
    Step 7: Prima scansione → "valid". Seconda scansione immediata → "already_scanned"
    con scanned_at valorizzato. Il payload membership deve contenere nome e cognome.

    Nota: questo test modifica stato nel DB (scrive un entrance_scan).
    Il teardown della fixture `entrance_seed` rimuove il documento.
    """
    member = entrance_seed.member_for_double_scan
    token = entrance_seed.scan_token

    # Prima scansione: deve passare
    first = entrance_service.validate_entry(member.membership_id, token)
    assert first["result"] == "valid", (
        f"Prima scansione attesa 'valid', ottenuto: {first['result']}"
    )

    # Seconda scansione immediata: deve essere bloccata
    second = entrance_service.validate_entry(member.membership_id, token)
    assert second["result"] == "already_scanned", (
        f"Seconda scansione attesa 'already_scanned', ottenuto: {second['result']}"
    )
    assert second["scanned_at"] is not None, (
        "scanned_at deve essere valorizzato per un membro già entrato"
    )
    assert second["membership"]["name"] == member.name
    assert second["membership"]["surname"] == member.surname


# ---------------------------------------------------------------------------
# Step 8 — Membro con membership non valida → rifiutato
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_member_with_invalid_subscription_rejected(entrance_seed, entrance_service):
    """
    Step 8: La membership esiste ma subscription_valid=False (scaduta / non attiva).
    Non avendo acquistato un biglietto, non esiste alcun participant record collegato
    → la scansione restituisce "invalid_no_purchase".

    Il sistema di ingresso si basa sull'acquisto del biglietto, non sullo stato
    della membership al momento della scansione: una tessera scaduta non avrebbe
    mai potuto completare l'acquisto.
    """
    member = entrance_seed.member_invalid_subscription
    result = entrance_service.validate_entry(
        member.membership_id, entrance_seed.scan_token
    )
    assert result["result"] == "invalid_no_purchase", (
        f"Atteso 'invalid_no_purchase' per membership non valida, "
        f"ottenuto: {result['result']}"
    )


# ---------------------------------------------------------------------------
# Extra — Token inesistente viene rifiutato in entrambi gli endpoint
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_nonexistent_token_rejected(entrance_seed, entrance_service):
    """
    Extra: Un token inventato non presente nel DB deve essere rifiutato sia
    da validate_entry che da verify_scan_token.
    """
    fake_token = "0000000000000000000000000000ffff"

    validate_result = entrance_service.validate_entry("any-membership-id", fake_token)
    assert validate_result["result"] == "invalid_token"

    verify_result = entrance_service.verify_scan_token(fake_token)
    assert verify_result["valid"] is False
    assert verify_result["reason"] == "not_found"
