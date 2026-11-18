"""OPS-03: trigger replay and delivery metadata, without live mail or PDF upload."""
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest

from config.firebase_config import db
from models import EventParticipant
from services.events.ticket_service import TicketService
from services.memberships.memberships_service import MembershipsService
from triggers import registration_trigger


@pytest.fixture
def notifications(monkeypatch):
    sent = []
    rendered = []

    def render(participant, event, path):
        rendered.append((participant, path))
        return SimpleNamespace(storage_path=path, public_url='https://example.com/stub.pdf',
                               buffer=BytesIO(b'PDF-STUB'))

    mail = SimpleNamespace(send=lambda message: sent.append(message) or True)
    ticket = TicketService(documents_service=SimpleNamespace(create_ticket_document=render),
                           mail_service_instance=mail)
    monkeypatch.setattr(registration_trigger, 'ticket_service', ticket)
    monkeypatch.setattr(registration_trigger, 'mail_service', mail)
    monkeypatch.setattr(registration_trigger, 'build_gender_lookup',
                        lambda: SimpleNamespace(lookup=lambda name: ('female', 0.9)))
    monkeypatch.setattr(registration_trigger, 'sync_participant_to_sender', lambda *a, **kw: None)
    monkeypatch.setattr(registration_trigger, 'sync_membership_to_sender', lambda *a, **kw: None)
    return SimpleNamespace(mail=mail, ticket=ticket, sent=sent, rendered=rendered)


def participant_ref(sample):
    participant = EventParticipant(id='notice-person', event_id=sample.event.id, name='Andrea',
                                   surname='Prova', email='notice@example.com', price=10,
                                   birthdate='01-01-1980', send_ticket_on_create=False)
    ref = db.document(f'participants/{sample.event.id}/participants_event/{participant.id}')
    ref.set(participant.to_firestore())
    return ref


@pytest.mark.parametrize('send', [False, True])
def test_ticket_delivery_does_not_overwrite_changes_during_pdf_generation(sample, notifications, send):
    ref = participant_ref(sample)
    before = ref.get().to_dict()
    original = notifications.ticket.documents_service.create_ticket_document

    def render_and_change(*args):
        document = original(*args)
        ref.update({'entered': True, 'price': 17, 'membershipId': 'current-member'})
        return document

    notifications.ticket.documents_service.create_ticket_document = render_and_change
    result = notifications.ticket.process_new_ticket(ref.id, before, send=send)

    assert result == {'success': True}
    data = ref.get().to_dict()
    assert (data['entered'], data['price'], data['membershipId']) == (True, 17, 'current-member')
    assert data['ticket_pdf_url'] == 'https://example.com/stub.pdf'
    assert data['ticket_sent'] is send
    assert len(notifications.rendered) == 1
    assert len(notifications.sent) == int(send)


def test_ticket_delivery_does_not_recreate_deleted_participant(sample, notifications):
    ref = participant_ref(sample)
    before = ref.get().to_dict()
    original = notifications.ticket.documents_service.create_ticket_document

    def render_and_delete(*args):
        document = original(*args)
        ref.delete()
        return document

    notifications.ticket.documents_service.create_ticket_document = render_and_delete
    result = notifications.ticket.process_new_ticket(ref.id, before, send=False)

    assert result['success'] is False
    assert not ref.get().exists
    assert notifications.sent == []


def test_pdf_only_generation_preserves_a_concurrent_confirmed_delivery(sample, notifications):
    ref = participant_ref(sample)
    before = ref.get().to_dict()
    original = notifications.ticket.documents_service.create_ticket_document

    def render_and_confirm(*args):
        document = original(*args)
        ref.update({'ticket_sent': True})
        return document

    notifications.ticket.documents_service.create_ticket_document = render_and_confirm
    assert notifications.ticket.process_new_ticket(ref.id, before, send=False) == {'success': True}
    assert ref.get().to_dict()['ticket_sent'] is True
    assert notifications.sent == []


@pytest.mark.parametrize('send', [False, True])
def test_participant_trigger_replay_preserves_gender_and_suppresses_duplicate_delivery(sample, notifications, send):
    ref = participant_ref(sample)
    ref.update({'send_ticket_on_create': send})
    event = SimpleNamespace(data=ref.get(), params={'eventId': sample.event.id, 'participantId': ref.id})

    registration_trigger.on_participant_created.__wrapped__(event)
    registration_trigger.on_participant_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert (data['gender'], data['gender_probability']) == ('male', 1.0)
    assert data['ticket_sent'] is send
    assert data['ticket_pdf_url'] == 'https://example.com/stub.pdf'
    assert len(notifications.sent) == int(send)
    # With sending disabled, replay is allowed to regenerate the PDF stub.
    assert len(notifications.rendered) == (1 if send else 2)


def test_uncertain_ticket_delivery_requires_manual_retry(sample, notifications):
    ref = participant_ref(sample)
    ref.update({'send_ticket_on_create': True})
    event = SimpleNamespace(data=ref.get(), params={'eventId': sample.event.id, 'participantId': ref.id})
    notifications.mail.send = lambda message: notifications.sent.append(message) or False

    registration_trigger.on_participant_created.__wrapped__(event)
    assert ref.get().to_dict()['ticket_sent'] is False

    notifications.mail.send = lambda message: notifications.sent.append(message) or True
    registration_trigger.on_participant_created.__wrapped__(event)
    assert len(notifications.sent) == 1
    assert ref.get().to_dict()['ticket_sent'] is False

    result = notifications.ticket.process_new_ticket(ref.id, ref.get().to_dict(), send=True)
    assert result == {'success': True}
    registration_trigger.on_participant_created.__wrapped__(event)

    assert ref.get().to_dict()['ticket_sent'] is True
    assert len(notifications.sent) == 2


def test_confirmed_email_with_failed_status_write_is_not_automatically_resent(sample, notifications, monkeypatch):
    ref = participant_ref(sample)
    ref.update({'send_ticket_on_create': True})
    event = SimpleNamespace(data=ref.get(), params={'eventId': sample.event.id, 'participantId': ref.id})

    def failed_write(*args):
        raise OSError('simulated status persistence failure')

    monkeypatch.setattr(notifications.ticket.participant_repository, 'update_ticket_delivery', failed_write,
                        raising=False)
    registration_trigger.on_participant_created.__wrapped__(event)
    registration_trigger.on_participant_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert data['ticket_sent'] is False
    assert data['ticket_delivery_started'] is True
    assert len(notifications.sent) == 1


def test_concurrent_ticket_triggers_send_only_once(sample, notifications):
    ref = participant_ref(sample)
    ref.update({'send_ticket_on_create': True})
    event = SimpleNamespace(data=ref.get(), params={'eventId': sample.event.id, 'participantId': ref.id})
    both_rendering = Barrier(2, timeout=5)
    original = notifications.ticket.documents_service.create_ticket_document

    def synchronized_render(*args):
        document = original(*args)
        both_rendering.wait()
        return document

    notifications.ticket.documents_service.create_ticket_document = synchronized_render
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(registration_trigger.on_participant_created.__wrapped__, event) for _ in range(2)]
        for future in futures:
            future.result(timeout=20)

    assert len(notifications.sent) == 1
    assert ref.get().to_dict()['ticket_sent'] is True


def test_concurrent_membership_triggers_send_only_once(sample, notifications):
    ref = db.document('memberships/' + sample.people[0].id)
    ref.update({'send_card_on_create': True, 'uid': 'existing-owner', 'wallet_pass_id': 'existing-pass'})
    both_read = Barrier(2, timeout=5)

    def read_before_claim():
        snapshot = ref.get()
        if not snapshot.to_dict().get('trigger_processed'):
            both_read.wait()
        return snapshot

    observed_ref = SimpleNamespace(get=read_before_claim, update=ref.update)
    event = SimpleNamespace(data=SimpleNamespace(reference=observed_ref), params={'membershipId': ref.id})
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(registration_trigger.on_membership_created.__wrapped__, event) for _ in range(2)]
        for future in futures:
            future.result(timeout=20)

    assert len(notifications.sent) == 1
    assert ref.get().to_dict()['membership_sent'] is True


@pytest.mark.parametrize('send', [False, True])
def test_membership_claim_retries_unrelated_writer_and_rechecks_current_data(sample, notifications, send):
    ref = db.document('memberships/' + sample.people[0].id)
    ref.update({'send_card_on_create': True, 'uid': 'existing-owner', 'wallet_pass_id': 'existing-pass'})
    changed = False

    def read_and_change_once():
        nonlocal changed
        snapshot = ref.get()
        if not changed:
            changed = True
            ref.update({'email': 'changed@example.com', 'send_card_on_create': send})
        return snapshot

    observed_ref = SimpleNamespace(get=read_and_change_once, update=ref.update)
    event = SimpleNamespace(data=SimpleNamespace(reference=observed_ref), params={'membershipId': ref.id})
    registration_trigger.on_membership_created.__wrapped__(event)

    data = ref.get().to_dict()
    assert data['trigger_processed'] is True
    assert data['membership_sent'] is send
    assert [message.to_email for message in notifications.sent] == (['changed@example.com'] if send else [])


def test_uncertain_membership_delivery_requires_manual_retry(sample, notifications):
    ref = db.document('memberships/' + sample.people[0].id)
    ref.update({'send_card_on_create': True, 'uid': 'existing-owner', 'wallet_pass_id': 'existing-pass',
                'wallet_url': 'https://example.com/existing-pass'})
    event = SimpleNamespace(data=ref.get(), params={'membershipId': ref.id})
    notifications.mail.send = lambda message: notifications.sent.append(message) or False

    registration_trigger.on_membership_created.__wrapped__(event)
    assert ref.get().to_dict()['membership_sent'] is False
    notifications.mail.send = lambda message: notifications.sent.append(message) or True
    registration_trigger.on_membership_created.__wrapped__(event)
    assert len(notifications.sent) == 1

    MembershipsService(mail_service_instance=notifications.mail).send_card(ref.id)
    registration_trigger.on_membership_created.__wrapped__(event)
    assert ref.get().to_dict()['membership_sent'] is True
    assert len(notifications.sent) == 2
