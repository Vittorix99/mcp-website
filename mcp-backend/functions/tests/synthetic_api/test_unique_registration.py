"""Q-08 revised: one nominative registration per member/event, before payment."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

from flask import request
import pytest

from api.admin import participants_api
from config.firebase_config import db
from tests.synthetic_api.test_deletion_integrity import database_state, free_registration
from tests.synthetic_api.test_purchase_entrance_stats import create_order, order_payload


@pytest.fixture
def registration_http(http):
    http.application.add_url_rule('/participants', 'create-participant-unique',
        lambda: participants_api.create_participant(request), methods=['POST'])
    http.application.add_url_rule('/participants', 'update-participant-unique',
        lambda: participants_api.update_participant(request), methods=['PUT'])
    return http


def manual_payload(sample, member=None):
    member = member or sample.people[0]
    return {'event_id': sample.event.id, 'name': member.name, 'surname': member.surname,
            'email': member.email, 'phone': member.phone, 'birthdate': member.birthdate,
            'membership_id': member.id, 'price': 0, 'payment_method': 'omaggio',
            'send_ticket_on_create': False}


@pytest.mark.parametrize('legacy_flag', [False, True])
def test_duplicate_checkout_payload_is_rejected_before_provider(http, sample, gateway, legacy_flag):
    db.document('events/' + sample.event.id).update({'allowDuplicates': legacy_flag})
    payload = order_payload(sample)
    payload['cart'][0]['participants'] = [payload['cart'][0]['participants'][0]] * 2
    before = database_state()
    response = http.post('/orders', json=payload)
    assert response.status_code == 400, response.get_json()
    assert (gateway.create_calls, gateway.capture_calls) == (0, 0)
    assert database_state() == before


@pytest.mark.parametrize('same', ['membership', 'email', 'phone'])
def test_admin_cannot_register_same_person_twice(registration_http, sample, same):
    payload = manual_payload(sample)
    assert registration_http.post('/participants', json=payload).status_code == 201
    if same != 'membership':
        payload.pop('membership_id')
    if same != 'email':
        payload['email'] = 'different@example.com'
    if same != 'phone':
        payload['phone'] = '+999123456'
    before = database_state()
    response = registration_http.post('/participants', json=payload)
    assert response.status_code == 409, response.get_json()
    assert database_state() == before


def test_membership_reassignment_rejects_duplicate_without_partial_edit(registration_http, sample):
    first = registration_http.post('/participants', json=manual_payload(sample)).get_json()['id']
    second = registration_http.post('/participants', json=manual_payload(sample, sample.people[1])).get_json()['id']
    before = database_state()
    result = registration_http.put('/participants', json={'event_id': sample.event.id,
        'participant_id': second, 'membership_id': sample.people[0].id, 'surname': 'Changed'})
    assert result.status_code == 409, result.get_json()
    assert database_state() == before
    # Linked identity edits now require the member page, even without a duplicate.
    result = registration_http.put('/participants', json={'event_id': sample.event.id,
        'participant_id': first, 'surname': 'Updated'})
    assert result.status_code == 409, result.get_json()
    assert database_state() == before


def test_pending_checkout_reserves_identity_as_well_as_seats(http, sample, gateway):
    first = create_order(http, sample)
    before = database_state()
    duplicate = http.post('/orders', json=order_payload(sample))
    assert duplicate.status_code == 409, duplicate.get_json()
    assert database_state() == before
    assert gateway.create_calls == 1
    assert http.post('/capture', json={'order_id': first}).status_code == 200
    assert gateway.capture_calls == 1


def test_admin_cannot_duplicate_pending_checkout(registration_http, sample, gateway):
    create_order(registration_http, sample)
    before = database_state()
    duplicate = registration_http.post('/participants', json=manual_payload(sample))
    assert duplicate.status_code == 409, duplicate.get_json()
    assert database_state() == before
    assert gateway.capture_calls == 0


def test_capture_rechecks_existing_registration_before_provider(http, sample, gateway):
    order_id = create_order(http, sample)
    free_registration(sample, 'imported-outside-normal-writer', sample.people[0].id)
    before = database_state()
    response = http.post('/capture', json={'order_id': order_id})
    assert response.status_code == 409, response.get_json()
    assert gateway.capture_calls == 0
    assert database_state() == before


def test_same_member_can_register_for_different_events(registration_http, sample):
    payload = manual_payload(sample)
    assert registration_http.post('/participants', json=payload).status_code == 201
    other = db.document('events/other-event')
    other.set(db.document('events/' + sample.event.id).get().to_dict())
    payload['event_id'] = other.id
    assert registration_http.post('/participants', json=payload).status_code == 201


def test_simultaneous_admin_writes_create_only_one_registration(registration_http, sample, monkeypatch):
    barrier, lock = Barrier(2), Lock()
    original_batch = db.batch
    commits = 0

    class Batch:
        def __init__(self):
            self.inner = original_batch()

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def commit(self, *args, **kwargs):
            nonlocal commits
            with lock:
                commits += 1
                overlap = commits <= 2
            if overlap:
                barrier.wait(timeout=15)
            return self.inner.commit(*args, **kwargs)

    monkeypatch.setattr(db, 'batch', Batch)
    payload = manual_payload(sample)

    def create(_):
        with registration_http.application.test_client() as client:
            return client.post('/participants', json=payload,
                headers={'Authorization': 'Bearer synthetic-test-admin'}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert sorted(responses) == [201, 409]
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 1


def test_reserving_checkout_loses_to_admin_insert_before_provider(registration_http, sample, gateway, monkeypatch):
    from api.public.event_payment_api import event_payment_service
    repo = event_payment_service.capacity_repository
    original_commit = repo._commit
    insert_once = True

    def insert_before_commit(*args, **kwargs):
        nonlocal insert_once
        if insert_once:
            insert_once = False
            assert registration_http.post('/participants', json=manual_payload(sample)).status_code == 201
        return original_commit(*args, **kwargs)

    monkeypatch.setattr(repo, '_commit', insert_before_commit)
    response = registration_http.post('/orders', json=order_payload(sample))
    assert response.status_code == 409, response.get_json()
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())


def test_admin_insert_loses_to_checkout_identity_reservation(registration_http, sample, gateway, monkeypatch):
    repo = participants_api.participants_service.participant_repository
    original_write = repo._write
    checkout_once = True

    def reserve_before_write(*args, **kwargs):
        nonlocal checkout_once
        if checkout_once:
            checkout_once = False
            create_order(registration_http, sample)
        return original_write(*args, **kwargs)

    monkeypatch.setattr(repo, '_write', reserve_before_write)
    response = registration_http.post('/participants', json=manual_payload(sample))
    assert response.status_code == 409, response.get_json()
    assert gateway.create_calls == 1 and gateway.capture_calls == 0
    assert not list(db.collection(f'participants/{sample.event.id}/participants_event').stream())


def test_simultaneous_checkouts_reserve_same_identity_only_once(http, sample, gateway, monkeypatch):
    from api.public.event_payment_api import event_payment_service
    repo = event_payment_service.capacity_repository
    original_commit = repo._commit
    barrier, lock = Barrier(2), Lock()
    attempts = 0

    def overlap_commit(*args, **kwargs):
        nonlocal attempts
        if kwargs.get('create'):
            with lock:
                attempts += 1
                overlap = attempts <= 2
            if overlap:
                barrier.wait(timeout=15)
        return original_commit(*args, **kwargs)

    monkeypatch.setattr(repo, '_commit', overlap_commit)

    def create(_):
        with http.application.test_client() as client:
            return client.post('/orders', json=order_payload(sample),
                headers={'Authorization': 'Bearer synthetic-test-admin'}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert sorted(responses) == [201, 409]
    assert gateway.create_calls == 1 and gateway.capture_calls == 0
    assert len(list(db.collection('orders').stream())) == 1


def test_merge_reference_collision_rejects_before_updating_other_events(http, sample):
    from repositories.participant_repository import ParticipantRepository

    event = db.document('events/' + sample.event.id).get().to_dict()
    db.document('events/a-first-event').set(event)
    db.document('events/z-last-event').set(event)
    source_id, target_id = [member.id for member in sample.people]
    for event_id, identifier, member_id in [('a-first-event', 'source', source_id),
            ('z-last-event', 'source', source_id), ('z-last-event', 'target', target_id)]:
        db.document(f'participants/{event_id}/participants_event/{identifier}').set({
            'membershipId': member_id, 'price': 0, 'payment_method': 'omaggio'})
    before = database_state()
    from errors.service_errors import ConflictError
    with pytest.raises(ConflictError):
        ParticipantRepository().update_membership_reference(source_id, target_id)
    assert database_state() == before


@pytest.mark.parametrize('stage', ['create', 'capture'])
def test_expired_member_with_different_registration_contacts_is_rejected_before_provider(http, sample, gateway, stage):
    member = sample.people[0]
    sample.people = [member]
    db.document('memberships/' + member.id).update({
        'membership_years': [sample.now.year - 1], 'subscription_valid': False})
    db.document('events/' + sample.event.id).update({'type': 'ONLY_MEMBERS'})
    db.document('membership_settings/price').set({'price_by_year': {str(sample.now.year): 5}})
    order_id = create_order(http, sample) if stage == 'capture' else None
    # Historical registration contacts differ from the member's current contact details.
    free_registration(sample, 'previous-registration', member.id)
    before = database_state()
    if stage == 'create':
        response = http.post('/orders', json=order_payload(sample))
        assert response.status_code == 409, response.get_json()
        assert gateway.create_calls == 0
    else:
        response = http.post('/capture', json={'order_id': order_id})
        assert response.status_code == 409, response.get_json()
    assert gateway.capture_calls == 0
    assert database_state() == before
