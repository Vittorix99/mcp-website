"""OPS-05 characterization for admin omaggio delivery on the demo emulator."""
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from flask import request

from config.firebase_config import db
from models import EventParticipant, PaymentMethod
from services.events.participants_service import ParticipantsService


@pytest.fixture
def omaggio_http(http):
    from api.admin import participants_api

    http.application.add_url_rule(
        "/omaggio", "synthetic-send-omaggio",
        lambda: participants_api.send_omaggio_emails(request), methods=["POST"],
    )
    return http


class RecordingMailService:
    def __init__(self, failed_recipients=(), on_send=None):
        self.failed_recipients = set(failed_recipients)
        self.messages = []
        self.on_send = on_send

    def send(self, message):
        self.messages.append(message)
        if self.on_send:
            self.on_send(message)
        return message.to_email not in self.failed_recipients


class StubDocumentsService:
    def __init__(self, error=None):
        self.error = error

    def create_ticket_document(self, participant, event, storage_path):
        if self.error:
            raise self.error
        return SimpleNamespace(storage_path=storage_path, public_url="https://stub.invalid/ticket.pdf",
                               buffer=BytesIO(b"PDF-STUB"))


def _participant(event_id, participant_id, *, email, payment_method=PaymentMethod.OMAGGIO,
                 sent=False, sent_at=None):
    participant = EventParticipant(
        id=participant_id,
        event_id=event_id,
        name=participant_id.title(),
        surname="Guest",
        email=email,
        phone="+390000000000",
        birthdate="10-01-1985",
        price=0 if payment_method == PaymentMethod.OMAGGIO else 20,
        payment_method=payment_method,
        send_ticket_on_create=False,
        omaggio_email_sent=sent,
        omaggio_email_sent_at=sent_at,
    )
    ref = db.document(f"participants/{event_id}/participants_event/{participant_id}")
    ref.set(participant.to_firestore(include_none=True))
    return ref


def _service(monkeypatch, mailer, *, documents_error=None):
    from api.admin import participants_api

    service = ParticipantsService(mail_service_instance=mailer)
    service.ticket_service.documents_service = StubDocumentsService(documents_error)
    monkeypatch.setattr(participants_api, "participants_service", service)
    return service


def test_bulk_omaggio_delivery_counters_persistence_and_retry(omaggio_http, sample, monkeypatch):
    failed_email = "provider-failure@example.com"
    sent_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    successful = _participant(sample.event.id, "bulk-success", email="success@example.com")
    already_sent = _participant(sample.event.id, "bulk-sent", email="already@example.com",
                                sent=True, sent_at=sent_at)
    missing_email = _participant(sample.event.id, "bulk-no-email", email="")
    provider_failed = _participant(sample.event.id, "bulk-provider-failure", email=failed_email)
    non_omaggio = _participant(sample.event.id, "bulk-cash", email="cash@example.com",
                               payment_method=PaymentMethod.CASH)
    before = {ref.id: ref.get().to_dict() for ref in
              (already_sent, missing_email, provider_failed, non_omaggio)}
    mailer = RecordingMailService({failed_email})
    _service(monkeypatch, mailer)

    response = omaggio_http.post("/omaggio", json={"event_id": sample.event.id,
                                            "entryTime": "21:30"})

    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {"sent": 1, "failed": 2, "skipped": 1, "total": 4,
                                   "mode": "bulk"}
    assert {message.to_email for message in mailer.messages} == {"success@example.com", failed_email}
    for message in mailer.messages:
        assert message.category == "omaggio"
        assert message.attachment.filename == "evento_inventato_participation.pdf"
        assert message.attachment.content == b"PDF-STUB"
    sent_data = successful.get().to_dict()
    assert sent_data["omaggio_email_sent"] is True
    assert isinstance(sent_data["omaggio_email_sent_at"], datetime)
    for ref in (already_sent, missing_email, provider_failed, non_omaggio):
        assert ref.get().to_dict() == before[ref.id]

    mailer.failed_recipients.clear()
    retry = omaggio_http.post("/omaggio", json={"event_id": sample.event.id,
                                        "entryTime": "21:30"})
    assert retry.status_code == 200, retry.get_json()
    assert retry.get_json() == {"sent": 1, "failed": 1, "skipped": 2, "total": 4,
                                "mode": "bulk"}
    assert [message.to_email for message in mailer.messages].count("success@example.com") == 1
    assert [message.to_email for message in mailer.messages].count(failed_email) == 2
    assert successful.get().to_dict()["omaggio_email_sent_at"] == sent_data["omaggio_email_sent_at"]
    assert isinstance(provider_failed.get().to_dict()["omaggio_email_sent_at"], datetime)
    assert missing_email.get().to_dict() == before[missing_email.id]
    assert non_omaggio.get().to_dict() == before[non_omaggio.id]


def test_single_omaggio_can_resend_when_skip_disabled(omaggio_http, sample, monkeypatch):
    sent_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    ref = _participant(sample.event.id, "single-sent", email="single@example.com",
                       sent=True, sent_at=sent_at)
    mailer = RecordingMailService()
    _service(monkeypatch, mailer)

    resend = omaggio_http.post("/omaggio", json={"event_id": sample.event.id,
                                         "participantId": ref.id,
                                         "skipAlreadySent": False})
    assert resend.status_code == 200, resend.get_json()
    assert resend.get_json() == {"sent": 1, "failed": 0, "skipped": 0, "total": 1,
                                 "mode": "single"}
    assert [message.to_email for message in mailer.messages] == ["single@example.com"]
    updated = ref.get().to_dict()
    assert updated["omaggio_email_sent"] is True
    assert isinstance(updated["omaggio_email_sent_at"], datetime)

    skipped = omaggio_http.post("/omaggio", json={"event_id": sample.event.id,
                                          "participantId": ref.id})
    assert skipped.status_code == 200, skipped.get_json()
    assert skipped.get_json() == {"sent": 0, "failed": 0, "skipped": 1, "total": 1,
                                  "mode": "single"}
    assert len(mailer.messages) == 1


def test_single_non_omaggio_or_missing_participant_returns_404(omaggio_http, sample, monkeypatch):
    non_omaggio = _participant(sample.event.id, "single-cash", email="cash@example.com",
                               payment_method=PaymentMethod.CASH)
    mailer = RecordingMailService()
    _service(monkeypatch, mailer)

    for participant_id in (non_omaggio.id, "missing-id"):
        response = omaggio_http.post("/omaggio", json={"event_id": sample.event.id,
                                               "participantId": participant_id})
        assert response.status_code == 404, response.get_json()
    assert mailer.messages == []


def test_empty_omaggio_list_returns_zero_counters(omaggio_http, sample, monkeypatch):
    mailer = RecordingMailService()
    _service(monkeypatch, mailer)

    response = omaggio_http.post("/omaggio", json={"event_id": sample.event.id})

    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {"sent": 0, "failed": 0, "skipped": 0, "total": 0,
                                   "mode": "bulk"}
    assert mailer.messages == []


def test_pdf_generation_exception_falls_back_to_email_without_attachment(omaggio_http, sample, monkeypatch):
    _participant(sample.event.id, "pdf-fallback", email="fallback@example.com")
    mailer = RecordingMailService()
    _service(monkeypatch, mailer, documents_error=RuntimeError("stub PDF failure"))

    response = omaggio_http.post("/omaggio", json={"event_id": sample.event.id})

    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {"sent": 1, "failed": 0, "skipped": 0, "total": 1,
                                   "mode": "bulk"}
    assert len(mailer.messages) == 1
    assert mailer.messages[0].to_email == "fallback@example.com"
    assert mailer.messages[0].category == "omaggio"
    assert mailer.messages[0].attachment is None


def test_delivery_flag_persistence_preserves_participant_changes_during_send(
        omaggio_http, sample, monkeypatch):
    ref = _participant(sample.event.id, "changed-during-send", email="changed@example.com")

    def change_participant_during_send(_message):
        ref.update({"entered": True, "price": 42, "membershipId": "member-added-during-send"})

    mailer = RecordingMailService(on_send=change_participant_during_send)
    _service(monkeypatch, mailer)

    response = omaggio_http.post("/omaggio", json={"event_id": sample.event.id})

    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {"sent": 1, "failed": 0, "skipped": 0, "total": 1,
                                   "mode": "bulk"}
    updated = ref.get().to_dict()
    assert updated["entered"] is True
    assert updated["price"] == 42
    assert updated["membershipId"] == "member-added-during-send"
    assert updated["omaggio_email_sent"] is True
