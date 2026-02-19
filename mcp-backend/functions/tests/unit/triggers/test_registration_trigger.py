import types
from io import BytesIO

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


class _DummyDoc:
    def __init__(self, url, path, payload=b"pdf"):
        self.public_url = url
        self.storage_path = path
        self.buffer = BytesIO(payload)


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
        }
    )
    event = types.SimpleNamespace(data=snap, params={"membershipId": membership_id})

    document = _DummyDoc(
        url="https://example.com/memberships/cards/mem-1.pdf",
        path="memberships/cards/mem-1.pdf",
    )

    class _DummyDocsService:
        def __init__(self):
            self.storage = None

        def create_membership_card(self, *_args, **_kwargs):
            return document

    called = {}

    def _fake_send(message):
        called["to"] = message.to_email
        called["subject"] = message.subject
        return True

    monkeypatch.setattr(registration_trigger, "DocumentsService", _DummyDocsService)
    monkeypatch.setattr(registration_trigger.mail_service, "send", _fake_send)
    monkeypatch.setattr(
        registration_trigger,
        "SubscribersClient",
        lambda: types.SimpleNamespace(sync_membership=lambda *args, **kwargs: None),
    )

    registration_trigger.on_membership_created.__wrapped__(event)

    assert any("card_url" in update for update in snap.reference.updates)
    assert any(update.get("membership_sent") is True for update in snap.reference.updates)
    assert called.get("to") == "mcpweb.test@gmail.com"
    assert called.get("subject") == "Tessera Associativa MCP"
