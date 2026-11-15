"""Q-08: registration rows share one membership/event entrance."""
import pytest

from config.firebase_config import db
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from tests.synthetic_api.test_purchase_entrance_stats import scan_token


@pytest.mark.parametrize('mode', ['scan', 'manual'])
def test_duplicate_registrations_share_entry_undo_and_reentry(http, completed, mode):
    event_id, member_id = completed.event.id, completed.people[0].id
    rows = db.collection(f'participants/{event_id}/participants_event')
    original = rows.document(member_id).get().to_dict()
    rows.document('duplicate').set(original)
    other_event = db.document(f'participants/other-event/participants_event/duplicate')
    other_event.set(original)
    purchase = db.document('purchases/' + completed.purchase.id)
    before_purchase = purchase.get().to_dict()
    token = scan_token(http, event_id)

    def enter():
        if mode == 'scan':
            return http.post('/scan', json={'scan_token': token, 'membership_id': member_id})
        return http.post('/manual-entry', json={
            'event_id': event_id, 'membership_id': member_id, 'entered': True})

    def assert_state(entered, count):
        documents = {row.id: row.to_dict() for row in rows.stream()}
        assert len(documents) == 3
        for identifier in (member_id, 'duplicate'):
            assert documents[identifier]['entered'] is entered
            assert bool(documents[identifier].get('entered_at')) is entered
        assert documents[member_id].get('entered_at') == documents['duplicate'].get('entered_at')
        assert not documents[completed.people[1].id].get('entered')
        assert other_event.get().to_dict() == original
        assert purchase.get().to_dict() == before_purchase
        assert len(list(db.collection(f'entrance_scans/{event_id}/scans').stream())) == count
        snapshot = AnalyticsSnapshotService().rebuild_event_snapshot(event_id)
        assert snapshot['kpis']['participants'] == 3
        funnel = http.get('/funnel', query_string={'event_id': event_id}).get_json()
        assert (funnel['enteredFlag'], funnel['scanned']) == (2 if entered else 0, count)

    result = enter()
    assert result.status_code == 200, result.get_json()
    assert result.get_json()['result'] == ('valid' if mode == 'scan' else 'entered')
    assert result.get_json()['participants_count'] == 3
    assert result.get_json()['entered_count'] == 1
    assert_state(True, 1)
    timestamps = {row.id: row.to_dict().get('entered_at') for row in rows.stream()}
    # An existing scan also aligns a registration added after the initial entrance.
    rows.document('duplicate').set(original)
    repeated = enter()
    assert repeated.get_json()['result'] == ('already_scanned' if mode == 'scan' else 'already_entered')
    assert repeated.get_json()['entered_count'] == 1
    assert_state(True, 1)
    assert rows.document(member_id).get().to_dict()['entered_at'] == timestamps[member_id]
    undone = http.post('/manual-entry', json={
        'event_id': event_id, 'membership_id': member_id, 'entered': False})
    assert undone.status_code == 200, undone.get_json()
    assert undone.get_json()['result'] == 'undone'
    assert_state(False, 0)
    assert enter().get_json()['entered_count'] == 1
    assert_state(True, 1)


@pytest.mark.parametrize('mode', ['scan', 'manual'])
@pytest.mark.parametrize('already_entered', [False, True])
def test_entry_finishing_after_undo_does_not_restore_registration_flags(http, completed, monkeypatch, mode, already_entered):
    from api.entrance.entrance_api import entrance_service

    event_id, member_id = completed.event.id, completed.people[0].id
    if already_entered:
        assert http.post('/manual-entry', json={
            'event_id': event_id, 'membership_id': member_id, 'entered': True}).status_code == 200
    repo = entrance_service.participant_repository
    original_sync = repo.sync_entered_by_membership_id
    undo_once = True

    def undo_before_sync(*args, **kwargs):
        nonlocal undo_once
        if undo_once:
            undo_once = False
            response = http.post('/manual-entry', json={
                'event_id': event_id, 'membership_id': member_id, 'entered': False})
            assert response.status_code == 200
        return original_sync(*args, **kwargs)

    monkeypatch.setattr(repo, 'sync_entered_by_membership_id', undo_before_sync)
    if mode == 'scan':
        token = scan_token(http, event_id)
        result = http.post('/scan', json={'scan_token': token, 'membership_id': member_id})
    else:
        result = http.post('/manual-entry', json={
            'event_id': event_id, 'membership_id': member_id, 'entered': True})
    assert result.status_code == 200, result.get_json()
    assert result.get_json()['entered_count'] == 0
    assert not db.document(f'entrance_scans/{event_id}/scans/{member_id}').get().exists
    participant = db.document(f'participants/{event_id}/participants_event/{member_id}').get().to_dict()
    assert participant['entered'] is False
    assert participant.get('entered_at') is None
