"""Q-07: protect receipt/entrance history and remove only free references."""
from flask import request
import pytest

from config.firebase_config import db
from api.admin import events_api, participants_api
from models import EventParticipant, PaymentMethod
from tests.synthetic_api.test_purchase_entrance_stats import scan_token


@pytest.fixture
def deletion_http(http):
    http.application.add_url_rule('/delete-event', 'delete-event',
        lambda: events_api.admin_delete_event(request), methods=['DELETE'])
    http.application.add_url_rule('/delete-participant', 'delete-participant',
        lambda: participants_api.delete_participant(request), methods=['DELETE'])
    return http


def delete(http, case, target):
    if target == 'event':
        return http.delete('/delete-event', json={'id': case.event.id})
    return http.delete('/delete-participant', json={
        'event_id': case.event.id, 'participant_id': case.people[0].id})


def database_state():
    from tests.synthetic_api.conftest import _document_paths
    return {path: db.document(path).get().to_dict() for path in _document_paths(db)}


@pytest.mark.parametrize('target', ['event', 'participant'])
@pytest.mark.parametrize('history', ['online', 'manual', 'scan', 'flag', 'timestamp', 'orphan_purchase'])
def test_delete_rejects_history_without_modifying_any_document(deletion_http, completed, target, history):
    case = completed
    member_id = case.people[0].id
    row = db.document(f'participants/{case.event.id}/participants_event/{member_id}')
    if history != 'online':
        db.document('purchases/' + case.purchase.id).delete()
        for item in db.collection(f'participants/{case.event.id}/participants_event').stream():
            item.reference.update({'purchase_id': None, 'price': 0, 'payment_method': 'omaggio'})
    if history == 'manual':
        row.update({'price': 12.5, 'payment_method': 'cash'})
    elif history == 'scan':
        db.document(f'entrance_scans/{case.event.id}/scans/{member_id}').set({'scanned_at': case.now})
    elif history == 'flag':
        row.update({'entered': True})
    elif history == 'timestamp':
        row.update({'entered_at': case.now})
    elif history == 'orphan_purchase':
        row.update({'purchase_id': 'missing-purchase'})
    before = database_state()
    result = delete(deletion_http, case, target)
    assert result.status_code == 409, result.get_json()
    assert database_state() == before


def free_registration(case, identifier, member_id=None):
    row = EventParticipant(id=identifier, event_id=case.event.id, name='Socio', surname='Prova',
        email='free@example.com', membership_id=member_id, price=0, payment_method=PaymentMethod.OMAGGIO,
        send_ticket_on_create=False)
    ref = db.document(f'participants/{case.event.id}/participants_event/{identifier}')
    ref.set(row.to_firestore())
    return ref


def test_delete_free_event_removes_children_and_membership_links(deletion_http, sample):
    case = sample
    free_registration(case, case.people[0].id, case.people[0].id)
    free_registration(case, 'second-free')
    member = db.document('memberships/' + case.people[0].id)
    member.update({'attended_events': [case.event.id, 'other-event']})
    # A stale member link must be cleaned even without a matching registration.
    stale_member = db.document('memberships/' + case.people[1].id)
    stale_member.update({'attended_events': [case.event.id]})
    token = scan_token(deletion_http, case.event.id)
    for collection in ('event_locations', 'event_guides', 'analytics_event'):
        db.document(f'{collection}/{case.event.id}').set({'free': True})
        db.document(f'{collection}/other-event').set({'keep': True})
    result = delete(deletion_http, case, 'event')
    assert result.status_code == 200, result.get_json()
    assert not db.document('events/' + case.event.id).get().exists
    assert not list(db.collection(f'participants/{case.event.id}/participants_event').stream())
    assert member.get().to_dict()['attended_events'] == ['other-event']
    assert stale_member.get().to_dict()['attended_events'] == []
    assert not db.document('scan_tokens/' + token).get().exists
    for collection in ('event_locations', 'event_guides', 'analytics_event'):
        assert not db.document(f'{collection}/{case.event.id}').get().exists
        assert db.document(f'{collection}/other-event').get().to_dict() == {'keep': True}


def test_delete_last_free_registration_clears_only_its_membership_event_link(deletion_http, sample):
    case = sample
    member_id = case.people[0].id
    free_registration(case, member_id, member_id)
    duplicate = free_registration(case, 'duplicate', member_id)
    member = db.document('memberships/' + member_id)
    member.update({'attended_events': [case.event.id, 'other-event']})
    assert delete(deletion_http, case, 'participant').status_code == 200
    assert member.get().to_dict()['attended_events'] == [case.event.id, 'other-event']
    result = deletion_http.delete('/delete-participant', json={
        'event_id': case.event.id, 'participant_id': duplicate.id})
    assert result.status_code == 200, result.get_json()
    assert member.get().to_dict()['attended_events'] == ['other-event']
    assert db.document('events/' + case.event.id).get().exists


@pytest.mark.parametrize('target', ['event', 'participant'])
@pytest.mark.parametrize('mode', ['scan', 'manual'])
def test_scan_cannot_recreate_history_after_free_registration_deletion(deletion_http, sample, monkeypatch, target, mode):
    from api.entrance.entrance_api import entrance_service

    case = sample
    member_id = case.people[0].id
    free_registration(case, member_id, member_id)
    token = scan_token(deletion_http, case.event.id)
    repo = entrance_service.entrance_scan_repository
    method = 'create_scan' if mode == 'scan' else 'create_manual'
    original_create = getattr(repo, method)

    def delete_before_create(*args, **kwargs):
        assert delete(deletion_http, case, target).status_code == 200
        return original_create(*args, **kwargs)

    monkeypatch.setattr(repo, method, delete_before_create)
    if mode == 'scan':
        response = deletion_http.post('/scan', json={'scan_token': token, 'membership_id': member_id})
    else:
        response = deletion_http.post('/manual-entry', json={
            'event_id': case.event.id, 'membership_id': member_id, 'entered': True})
    assert response.status_code == 404, response.get_json()
    assert not list(db.collection(f'entrance_scans/{case.event.id}/scans').stream())


@pytest.mark.parametrize('target', ['event', 'participant'])
@pytest.mark.parametrize('price,method', [(5, 'iban'), (5, 'private_paypal'),
    (5, 'website'), (5, 'unknown'), ('NaN', 'cash'), (-5, 'cash'), ('broken', 'cash')])
def test_delete_cannot_discard_uncertain_or_nonzero_amounts(deletion_http, sample, target, price, method):
    ref = free_registration(sample, sample.people[0].id, sample.people[0].id)
    ref.update({'price': price, 'payment_method': method})
    before = database_state()
    result = delete(deletion_http, sample, target)
    assert result.status_code == 409, result.get_json()
    assert database_state() == before


@pytest.mark.parametrize('state', ['REFUNDED', 'FAILED'])
def test_changed_purchase_status_does_not_allow_event_history_deletion(deletion_http, completed, state):
    db.document('purchases/' + completed.purchase.id).update({'status': state, 'capture_status': state})
    for row in db.collection(f'participants/{completed.event.id}/participants_event').stream():
        row.reference.delete()
    before = database_state()
    assert delete(deletion_http, completed, 'event').status_code == 409
    assert database_state() == before


def test_participant_with_missing_purchase_link_still_protects_member_receipt(deletion_http, completed):
    row = db.document(f'participants/{completed.event.id}/participants_event/{completed.people[0].id}')
    row.update({'purchase_id': None, 'price': 0, 'payment_method': 'omaggio'})
    before = database_state()
    result = delete(deletion_http, completed, 'participant')
    assert result.status_code == 409, result.get_json()
    assert database_state() == before


@pytest.mark.parametrize('state', ['reserved', 'capturing', 'consumed'])
def test_event_with_active_or_uncertain_reservation_is_not_deleted(deletion_http, sample, state):
    from datetime import timedelta
    db.document(f'event_capacity/{sample.event.id}/reservations/hold').set({
        'state': state, 'expiresAt': sample.now + timedelta(minutes=10), 'count': 1})
    before = database_state()
    assert delete(deletion_http, sample, 'event').status_code == 409
    assert database_state() == before


def test_oversized_free_event_cleanup_is_rejected_without_partial_deletes(deletion_http, sample):
    batch = db.batch()
    for index in range(401):
        batch.set(db.document(f'participants/{sample.event.id}/participants_event/free-{index}'),
                  {'price': 0, 'payment_method': 'omaggio'})
    batch.commit()
    before = database_state()
    assert delete(deletion_http, sample, 'event').status_code == 409
    assert database_state() == before


def test_token_generation_cannot_leave_reference_after_free_event_deletion(deletion_http, sample, monkeypatch):
    from api.entrance.entrance_api import entrance_service

    repo = entrance_service.scan_token_repository
    original_create = repo.create

    def delete_before_create(*args, **kwargs):
        assert delete(deletion_http, sample, 'event').status_code == 200
        return original_create(*args, **kwargs)

    monkeypatch.setattr(repo, 'create', delete_before_create)
    response = deletion_http.post('/scanner-token', json={'event_id': sample.event.id})
    assert response.status_code == 404, response.get_json()
    assert not list(db.collection('scan_tokens').stream())


@pytest.mark.parametrize('target', ['event', 'participant'])
def test_free_creation_cannot_restore_member_link_after_concurrent_delete(deletion_http, sample, monkeypatch, target):
    deletion_http.application.add_url_rule('/create-participant', 'create-participant',
        lambda: participants_api.create_participant(request), methods=['POST'])
    repo = participants_api.participants_service.participant_repository
    original_create = repo.create_from_model

    def delete_after_create(event_id, participant):
        identifier = original_create(event_id, participant)
        if target == 'event':
            result = delete(deletion_http, sample, 'event')
        else:
            result = deletion_http.delete('/delete-participant', json={
                'event_id': event_id, 'participant_id': identifier})
        assert result.status_code == 200, result.get_json()
        return identifier

    monkeypatch.setattr(repo, 'create_from_model', delete_after_create)
    member = sample.people[0]
    response = deletion_http.post('/create-participant', json={
        'event_id': sample.event.id, 'name': member.name, 'surname': member.surname,
        'email': member.email, 'phone': member.phone, 'birthdate': member.birthdate,
        'price': 0, 'payment_method': 'omaggio', 'send_ticket_on_create': False})
    assert response.status_code == 201, response.get_json()
    assert sample.event.id not in db.document('memberships/' + member.id).get().to_dict().get('attended_events', [])


@pytest.mark.parametrize('in_flight', [False, True])
def test_deleted_event_stays_out_of_analytics_index_after_rebuild(deletion_http, sample, in_flight):
    from services.core.analytics_snapshot_service import AnalyticsSnapshotService
    service = AnalyticsSnapshotService()
    snapshot = service.rebuild_event_snapshot(sample.event.id)
    assert delete(deletion_http, sample, 'event').status_code == 200
    if in_flight:
        # A rebuild read the complete event before the deletion committed.
        service.analytics_snapshot_repository.set_event_snapshot(sample.event.id, snapshot)
    else:
        assert service.rebuild_event_snapshot(sample.event.id)['exists'] is False
    assert service.get_event_snapshot(sample.event.id)['exists'] is False
    assert service.get_events_index()['events'] == []
