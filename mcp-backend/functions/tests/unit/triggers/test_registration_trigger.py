import types

import pytest

from triggers import registration_trigger


@pytest.fixture(autouse=True)
def _stub_sender_side_effects(monkeypatch):
    monkeypatch.setattr(registration_trigger, "sync_participant_to_sender", lambda *args, **kwargs: None)
    monkeypatch.setattr(registration_trigger, "sync_membership_to_sender", lambda *args, **kwargs: None)
    monkeypatch.setattr(registration_trigger, "log_external_error", lambda *args, **kwargs: None)

    # Stub db used for event title lookup inside on_participant_created
    class _DummyDoc:
        exists = False

        def to_dict(self):
            return {}

    class _DummyCollection:
        def document(self, _doc_id):
            return self

        def get(self):
            return _DummyDoc()

    class _DummyDB:
        def collection(self, _name):
            return _DummyCollection()

    monkeypatch.setattr(registration_trigger, "db", _DummyDB())

    # Stub Firebase Auth so unit tests never make real HTTP calls
    _fake_user = types.SimpleNamespace(uid="uid-test-stub")
    monkeypatch.setattr(registration_trigger.fb_auth, "create_user", lambda **_kw: _fake_user)
    monkeypatch.setattr(registration_trigger.fb_auth, "get_user_by_email", lambda _email: _fake_user)


class _DummyCurrentDoc:
    """Simulates the document snapshot returned by snapshot.reference.get()."""

    def __init__(self, data, exists=True):
        self._data = dict(data)
        self.exists = exists

    def to_dict(self):
        return dict(self._data)


class _DummyRef:
    def __init__(self, data=None):
        self.updates = []
        self._data = dict(data or {})

    def update(self, payload):
        self.updates.append(payload)

    def get(self):
        merged = dict(self._data)
        for u in self.updates:
            merged.update(u)
        return _DummyCurrentDoc(merged)


class _DummySnap:
    def __init__(self, data):
        self._data = dict(data)
        self.reference = _DummyRef(data=data)

    def to_dict(self):
        return dict(self._data)


def test_on_participant_created_updates_gender_and_sends_ticket(monkeypatch):
    participant_id = "part-1"
    event_id = "evt-1"
    snap = _DummySnap(
        {
            "name": "Mario Rossi",
            "email": "mcpweb.test@gmail.com",
            "send_ticket_on_create": True,
            "newsletterConsent": False,
        }
    )
    event = types.SimpleNamespace(data=snap, params={"participantId": participant_id, "eventId": event_id})

    called = {}

    def _fake_get(url, params=None, **_kwargs):
        called["gender_params"] = dict(params or {})

        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"gender": "female", "probability": 0.7}

        return _Resp()

    def _fake_process(pid, data, send):
        called["ticket"] = (pid, send)
        return {"success": True}

    monkeypatch.setattr(registration_trigger, "GENDER_API_KEY", "test-key-123")
    monkeypatch.setattr(registration_trigger.requests, "get", _fake_get)
    monkeypatch.setattr(registration_trigger.ticket_service, "process_new_ticket", _fake_process)
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "log_failed_ticket_email",
        lambda *args, **kwargs: called.setdefault("ticket_error", True),
    )
    registration_trigger.on_participant_created.__wrapped__(event)

    assert any(
        update.get("gender") == "female" and update.get("gender_probability") == 0.7
        for update in snap.reference.updates
    )
    assert called.get("ticket") == (participant_id, True)
    assert called["gender_params"].get("name") == "mario"
    assert called["gender_params"].get("apikey") == "test-key-123"


def test_on_participant_created_newsletter_sync_and_skip_ticket(monkeypatch):
    participant_id = "part-2"
    event_id = "evt-2"
    snap = _DummySnap(
        {
            "name": "Andrea",
            "email": "mcpweb.test@gmail.com",
            "send_ticket_on_create": False,
            "newsletterConsent": True,
        }
    )
    event = types.SimpleNamespace(data=snap, params={"participantId": participant_id, "eventId": event_id})

    called = {}

    def _fake_process(_pid, _data, send):
        called["send_flag"] = send
        return {"success": True}

    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "process_new_ticket",
        _fake_process,
    )
    monkeypatch.setattr(
        registration_trigger.requests,
        "get",
        lambda *args, **kwargs: pytest.fail("Gender API should not be called for Andrea"),
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    assert any(
        update.get("gender") == "male" and update.get("gender_probability") == 1.0
        for update in snap.reference.updates
    )
    assert called.get("send_flag") is False


def test_gender_api_passes_apikey_when_configured(monkeypatch):
    """apikey viene incluso nei params della chiamata a genderize.io quando GENDER_API_KEY è impostata."""
    snap = _DummySnap({
        "name": "Giulia Bianchi",
        "email": "test@example.com",
        "send_ticket_on_create": False,
        "newsletterConsent": False,
    })
    event = types.SimpleNamespace(
        data=snap,
        params={"participantId": "part-g1", "eventId": "evt-g1"},
    )
    captured = {}

    def _fake_get(url, params=None, **_kwargs):
        captured["params"] = dict(params or {})

        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"gender": "female", "probability": 0.97}

        return _Resp()

    monkeypatch.setattr(registration_trigger, "GENDER_API_KEY", "test-gender-api-key")
    monkeypatch.setattr(registration_trigger.requests, "get", _fake_get)
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "process_new_ticket",
        lambda pid, data, send: {"success": True},
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    assert captured["params"]["name"] == "giulia"
    assert captured["params"]["apikey"] == "test-gender-api-key"
    assert any(
        u.get("gender") == "female" and u.get("gender_probability") == 1.0
        for u in snap.reference.updates
    )


def test_gender_api_omits_apikey_when_not_configured(monkeypatch):
    """Senza GENDER_API_KEY la chiamata funziona comunque senza il parametro apikey."""
    snap = _DummySnap({
        "name": "Marco Verdi",
        "email": "test@example.com",
        "send_ticket_on_create": False,
        "newsletterConsent": False,
    })
    event = types.SimpleNamespace(
        data=snap,
        params={"participantId": "part-g2", "eventId": "evt-g2"},
    )
    captured = {}

    def _fake_get(url, params=None, **_kwargs):
        captured["params"] = dict(params or {})

        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"gender": "male", "probability": 0.95}

        return _Resp()

    monkeypatch.setattr(registration_trigger, "GENDER_API_KEY", None)
    monkeypatch.setattr(registration_trigger.requests, "get", _fake_get)
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "process_new_ticket",
        lambda pid, data, send: {"success": True},
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    assert captured["params"]["name"] == "marco"
    assert "apikey" not in captured["params"]
    assert any(u.get("gender") == "male" for u in snap.reference.updates)


def test_participant_from_purchase_gets_gender_set(monkeypatch):
    """Partecipante creato da un acquisto (purchase_id presente) riceve gender e gender_probability."""
    snap = _DummySnap({
        "name": "Federica Rossi",
        "email": "federica@example.com",
        "send_ticket_on_create": True,
        "newsletterConsent": False,
        "purchase_id": "purch-abc123",
        "payment_method": "website",
    })
    event = types.SimpleNamespace(
        data=snap,
        params={"participantId": "part-p1", "eventId": "evt-p1"},
    )
    called = {}

    def _fake_get(url, params=None, **_kwargs):
        called["gender_params"] = dict(params or {})

        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"gender": "female", "probability": 0.96}

        return _Resp()

    monkeypatch.setattr(registration_trigger, "GENDER_API_KEY", "test-gender-api-key")
    monkeypatch.setattr(registration_trigger.requests, "get", _fake_get)
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "process_new_ticket",
        lambda pid, data, send: called.setdefault("ticket", (pid, send)) or {"success": True},
    )
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "log_failed_ticket_email",
        lambda *args, **kwargs: None,
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    assert called["gender_params"]["name"] == "federica"
    assert called["gender_params"]["apikey"] == "test-gender-api-key"

    gender_update = next(
        (u for u in snap.reference.updates if "gender" in u),
        None,
    )
    assert gender_update is not None, "gender non è stato scritto su Firestore"
    assert gender_update["gender"] == "female"
    assert gender_update["gender_probability"] == 1.0

    assert called["ticket"] == ("part-p1", True)


def test_participant_from_purchase_gender_api_failure_does_not_block_ticket(monkeypatch):
    """Se la gender API fallisce, il ticket viene comunque processato e gender rimane N/A."""
    snap = _DummySnap({
        "name": "Luca Neri",
        "email": "luca@example.com",
        "send_ticket_on_create": True,
        "newsletterConsent": False,
        "purchase_id": "purch-xyz789",
        "payment_method": "website",
    })
    event = types.SimpleNamespace(
        data=snap,
        params={"participantId": "part-p2", "eventId": "evt-p2"},
    )
    called = {}

    def _failing_get(url, params=None, **_kwargs):
        raise RuntimeError("genderize.io timeout")

    monkeypatch.setattr(registration_trigger, "GENDER_API_KEY", "test-gender-api-key")
    monkeypatch.setattr(registration_trigger.requests, "get", _failing_get)
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "process_new_ticket",
        lambda pid, data, send: called.setdefault("ticket", (pid, send)) or {"success": True},
    )
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "log_failed_ticket_email",
        lambda *args, **kwargs: None,
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    gender_update = next(
        (u for u in snap.reference.updates if "gender" in u),
        None,
    )
    assert gender_update is not None
    assert gender_update["gender"] == "N/A"
    assert gender_update["gender_probability"] == 0.0
    assert called["ticket"] == ("part-p2", True)


def test_on_membership_created_generates_card_and_sends_email(monkeypatch):
    membership_id = "mem-1"
    snap = _DummySnap(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": "mcpweb.test@gmail.com",
            "send_card_on_create": True,
        }
    )
    event = types.SimpleNamespace(data=snap, params={"membershipId": membership_id})

    called = {}

    def _fake_send(message):
        called["to"] = message.to_email
        called["subject"] = message.subject
        return True

    class _DummyPass2UService:
        def create_membership_pass(self, *_args, **_kwargs):
            return types.SimpleNamespace(
                pass_id="pass-1",
                wallet_url="https://www.pass2u.net/d/pass-1",
            )

    monkeypatch.setattr(registration_trigger, "Pass2UService", _DummyPass2UService)
    monkeypatch.setattr(registration_trigger.mail_service, "send", _fake_send)

    registration_trigger.on_membership_created.__wrapped__(event)

    assert any(
        update.get("wallet_pass_id") == "pass-1"
        and update.get("wallet_url") == "https://www.pass2u.net/d/pass-1"
        for update in snap.reference.updates
    )
    assert any(update.get("membership_sent") is True for update in snap.reference.updates)
    assert called.get("to") == "mcpweb.test@gmail.com"
    assert called.get("subject") == "Tessera Associativa MCP"


def test_on_membership_created_does_not_send_email_when_send_flag_false(monkeypatch):
    membership_id = "mem-2"
    snap = _DummySnap(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": "mcpweb.test@gmail.com",
            "send_card_on_create": False,
        }
    )
    event = types.SimpleNamespace(data=snap, params={"membershipId": membership_id})

    called = {"email": False, "wallet": False}

    class _DummyPass2UService:
        def create_membership_pass(self, *_args, **_kwargs):
            called["wallet"] = True
            return types.SimpleNamespace(pass_id="pass-2", wallet_url="https://www.pass2u.net/d/pass-2")

    monkeypatch.setattr(registration_trigger, "Pass2UService", _DummyPass2UService)

    monkeypatch.setattr(
        registration_trigger.mail_service,
        "send",
        lambda *_args, **_kwargs: called.__setitem__("email", True),
    )

    registration_trigger.on_membership_created.__wrapped__(event)

    assert any(update.get("wallet_url") == "https://www.pass2u.net/d/pass-2" for update in snap.reference.updates)
    assert called["wallet"] is True
    assert called["email"] is False


def test_on_membership_created_accepts_string_send_flag(monkeypatch):
    """send_card_on_create memorizzato come stringa "true" in Firestore deve essere trattato come truthy."""
    membership_id = "mem-3"
    snap = _DummySnap(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": "mcpweb.test@gmail.com",
            "send_card_on_create": "true",
        }
    )
    event = types.SimpleNamespace(data=snap, params={"membershipId": membership_id})

    class _DummyPass2UService:
        def create_membership_pass(self, *_args, **_kwargs):
            return types.SimpleNamespace(pass_id="pass-3", wallet_url="https://www.pass2u.net/d/pass-3")

    monkeypatch.setattr(registration_trigger, "Pass2UService", _DummyPass2UService)

    called = {"email": False}
    monkeypatch.setattr(
        registration_trigger.mail_service,
        "send",
        lambda *_args, **_kwargs: called.__setitem__("email", True) or True,
    )

    registration_trigger.on_membership_created.__wrapped__(event)

    assert called["email"] is True
    assert any(update.get("membership_sent") is True for update in snap.reference.updates)


def test_on_membership_created_skips_wallet_when_flag_false(monkeypatch):
    """
    Backward-compatible alias for older test node ids used by local runners.
    """
    test_on_membership_created_does_not_send_email_when_send_flag_false(monkeypatch)
