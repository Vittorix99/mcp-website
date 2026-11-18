"""OPS-06: provider policy through real triggers and emulator persistence."""
import importlib
from io import BytesIO
from types import SimpleNamespace

import pytest
import requests

from config.firebase_config import db
from config.runtime_settings import load_runtime_settings
from models import EventParticipant
from services.events.ticket_service import TicketService
from services.gender import gender_service
from services.memberships import pass2u_service
from services.sender import sender_sync
from triggers import registration_trigger

mail_module = importlib.import_module('services.communications.mail_service')


@pytest.fixture(autouse=True)
def no_provider_http(monkeypatch):
    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append(True)
        raise AssertionError('Provider HTTP is forbidden in OPS-06')

    monkeypatch.setattr(requests.sessions.Session, 'request', forbidden)
    yield
    # Services may catch exceptions, so checking the attempts is essential.
    assert attempts == []


def configure(monkeypatch, *, wallet='disabled', gender='fake'):
    settings = load_runtime_settings({'MCP_ENV': 'test', 'PASS2U_MODE': wallet, 'GENDER_MODE': gender})
    for module in (gender_service, pass2u_service, sender_sync):
        monkeypatch.setattr(module, 'get_runtime_settings', lambda: settings)
    monkeypatch.setattr(registration_trigger, 'get_runtime_settings', lambda: settings)
    mail = mail_module.build_mail_service(settings)
    monkeypatch.setattr(registration_trigger, 'mail_service', mail)

    def render(participant, event, path):
        return SimpleNamespace(storage_path=path, public_url='https://example.com/ops06-stub.pdf',
                               buffer=BytesIO(b'PDF-STUB'))

    monkeypatch.setattr(registration_trigger, 'ticket_service', TicketService(
        documents_service=SimpleNamespace(create_ticket_document=render), mail_service_instance=mail))
    return mail


def member_event(sample):
    ref = db.document('memberships/' + sample.people[0].id)
    # This scenario checks providers, not Auth provisioning; use an already bound synthetic member.
    ref.update({'uid': 'ops06-existing-owner', 'send_card_on_create': False})
    event = SimpleNamespace(data=ref.get(), params={'membershipId': ref.id})
    return ref, event


@pytest.mark.parametrize('wallet', ['disabled', 'fake'])
def test_member_trigger_respects_wallet_policy_and_disabled_sender(sample, monkeypatch, wallet):
    mail = configure(monkeypatch, wallet=wallet)
    ref, event = member_event(sample)
    before = ref.get().to_dict()

    registration_trigger.on_membership_created.__wrapped__(event)
    registration_trigger.on_membership_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert data['trigger_processed'] is True
    assert data['membership_sent'] is False
    assert mail.sent_messages == []
    if wallet == 'disabled':
        assert {k: v for k, v in data.items() if k != 'trigger_processed'} == before
    else:
        assert data['wallet_pass_id'].startswith('FAKE-')
        assert data['wallet_url'] == f'http://127.0.0.1:3000/local-wallet/{ref.id}'
        assert {k: v for k, v in data.items() if k not in
                ('trigger_processed', 'wallet_pass_id', 'wallet_url')} == before


@pytest.mark.parametrize('gender,name,want_gender,want_probability', [
    ('fake', 'Giulia', 'female', 1.0),
    ('fake', 'Andrea', 'male', 1.0),
    ('fake', 'Unknown', 'N/A', 0.0),
    ('disabled', 'Giulia', 'N/A', 0.0),
    ('disabled', 'Andrea', 'N/A', 0.0),
])
def test_participant_trigger_respects_gender_policy_without_sender_or_mail(
        sample, monkeypatch, gender, name, want_gender, want_probability):
    mail = configure(monkeypatch, gender=gender)
    participant = EventParticipant(id='ops06-person', event_id=sample.event.id, name=name,
                                   surname='Prova', email='ops06-person@example.com', price=17,
                                   send_ticket_on_create=False, newsletter_consent=True)
    ref = db.document(f'participants/{sample.event.id}/participants_event/{participant.id}')
    ref.set(participant.to_firestore())
    before = ref.get().to_dict()
    event = SimpleNamespace(data=ref.get(), params={'eventId': sample.event.id, 'participantId': ref.id})

    registration_trigger.on_participant_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert (data['gender'], data['gender_probability']) == (want_gender, want_probability)
    assert data['ticket_pdf_url'] == 'https://example.com/ops06-stub.pdf'
    assert data['ticket_sent'] is False
    assert mail.sent_messages == []
    assert {k: v for k, v in data.items() if k not in ('gender', 'gender_probability', 'ticket_pdf_url')} == {
        k: v for k, v in before.items() if k not in ('gender', 'gender_probability', 'ticket_pdf_url')}


@pytest.mark.parametrize('raises', [False, True])
def test_wallet_failure_keeps_membership_and_binding(sample, monkeypatch, raises):
    mail = configure(monkeypatch)
    ref, event = member_event(sample)
    before = ref.get().to_dict()

    def failed_wallet(*args):
        if raises:
            raise RuntimeError('synthetic wallet failure')
        return None

    monkeypatch.setattr(registration_trigger, 'build_pass2u_service',
                        lambda: SimpleNamespace(create_membership_pass=failed_wallet))
    registration_trigger.on_membership_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert data['trigger_processed'] is True
    assert {k: v for k, v in data.items() if k != 'trigger_processed'} == before
    assert mail.sent_messages == []


def test_gender_failure_keeps_participant_and_generates_ticket_without_sending(sample, monkeypatch):
    mail = configure(monkeypatch)
    participant = EventParticipant(id='ops06-gender-failure', event_id=sample.event.id, name='Giulia',
                                   email='ops06-failure@example.com', price=17, entered=True,
                                   membership_id=sample.people[0].id, send_ticket_on_create=False)
    ref = db.document(f'participants/{sample.event.id}/participants_event/{participant.id}')
    ref.set(participant.to_firestore())

    def failed_lookup(name):
        raise RuntimeError('synthetic gender failure')

    monkeypatch.setattr(registration_trigger, 'build_gender_lookup',
                        lambda: SimpleNamespace(lookup=failed_lookup))
    event = SimpleNamespace(data=ref.get(), params={'eventId': sample.event.id, 'participantId': ref.id})
    registration_trigger.on_participant_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert (data['gender'], data['gender_probability']) == ('N/A', 0.0)
    assert (data['entered'], data['price'], data['membershipId']) == (True, 17, sample.people[0].id)
    assert data['ticket_pdf_url'] == 'https://example.com/ops06-stub.pdf'
    assert data['ticket_sent'] is False
    assert mail.sent_messages == []
