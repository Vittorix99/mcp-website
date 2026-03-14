import types

import pytest

from triggers import registration_trigger


class _DummyRef:
    def __init__(self):
        self.updates = []

    def update(self, payload):
        self.updates.append(payload)


class _DummySnap:
    def __init__(self, data):
        self._data = dict(data)
        self.reference = _DummyRef()

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
        called["gender_api"] = params.get("name") if params else None

        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"gender": "female", "probability": 0.7}

        return _Resp()

    def _fake_process(pid, data, send):
        called["ticket"] = (pid, send)
        return {"success": True}

    monkeypatch.setattr(registration_trigger.requests, "get", _fake_get)
    monkeypatch.setattr(registration_trigger.ticket_service, "process_new_ticket", _fake_process)
    monkeypatch.setattr(
        registration_trigger.ticket_service,
        "log_failed_ticket_email",
        lambda *args, **kwargs: called.setdefault("ticket_error", True),
    )
    monkeypatch.setattr(
        registration_trigger,
        "SubscribersClient",
        lambda: types.SimpleNamespace(
            sync_newsletter_consent=lambda *args, **kwargs: called.setdefault("newsletter", True)
        ),
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    assert any(
        update.get("gender") == "female" and update.get("gender_probability") == 0.7
        for update in snap.reference.updates
    )
    assert called.get("ticket") == (participant_id, True)
    assert "newsletter" not in called


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
    monkeypatch.setattr(
        registration_trigger,
        "SubscribersClient",
        lambda: types.SimpleNamespace(
            sync_newsletter_consent=lambda *args, **kwargs: called.setdefault("newsletter", True)
        ),
    )

    registration_trigger.on_participant_created.__wrapped__(event)

    assert any(
        update.get("gender") == "male" and update.get("gender_probability") == 1.0
        for update in snap.reference.updates
    )
    assert called.get("newsletter") is True
    assert called.get("send_flag") is False


def test_on_membership_created_generates_card_and_sends_email(monkeypatch):
    membership_id = "mem-1"
    snap = _DummySnap(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": "mcpweb.test@gmail.com",
            "send_card_on_create": True,
            "create_wallet_on_create": True,
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

    monkeypatch.setattr("services.memberships.pass2u_service.Pass2UService", _DummyPass2UService)
    monkeypatch.setattr(registration_trigger.mail_service, "send", _fake_send)
    monkeypatch.setattr(
        registration_trigger,
        "SubscribersClient",
        lambda: types.SimpleNamespace(sync_membership=lambda *args, **kwargs: None),
    )

    registration_trigger.on_membership_created.__wrapped__(event)

    assert any(
        update.get("wallet_pass_id") == "pass-1"
        and update.get("wallet_url") == "https://www.pass2u.net/d/pass-1"
        for update in snap.reference.updates
    )
    assert any(update.get("membership_sent") is True for update in snap.reference.updates)
    assert called.get("to") == "mcpweb.test@gmail.com"
    assert called.get("subject") == "Tessera Associativa MCP"


def test_on_membership_created_skips_wallet_when_flag_false(monkeypatch):
    membership_id = "mem-2"
    snap = _DummySnap(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": "mcpweb.test@gmail.com",
            "send_card_on_create": False,
            "create_wallet_on_create": False,
        }
    )
    event = types.SimpleNamespace(data=snap, params={"membershipId": membership_id})

    monkeypatch.setattr(
        "services.memberships.pass2u_service.Pass2UService",
        lambda: pytest.fail("Pass2UService should not be called when create_wallet_on_create=False"),
    )

    called = {"email": False}
    monkeypatch.setattr(
        registration_trigger.mail_service,
        "send",
        lambda *_args, **_kwargs: called.__setitem__("email", True),
    )
    monkeypatch.setattr(
        registration_trigger,
        "SubscribersClient",
        lambda: types.SimpleNamespace(sync_membership=lambda *args, **kwargs: None),
    )

    registration_trigger.on_membership_created.__wrapped__(event)

    assert not any("wallet_url" in update or "wallet_pass_id" in update for update in snap.reference.updates)
    assert called["email"] is False
