"""Matrix slice: HTTP handlers + real emulator repositories; admin auth is simulated.

Financial expected values below are literals, not computed by app analytics.
No test claims real PayPal, deployed HTTP transport, triggers or JWT verification.
"""
from datetime import timedelta

import pytest

from config.firebase_config import db
from services.core.analytics_snapshot_service import AnalyticsSnapshotService


# Keep scenarios independent: a production status omission must not remove a test.
INVALID_PURCHASE_STATES = ('FAILED', 'CANCELLED', 'VOIDED', 'REFUNDED', 'DECLINED', 'ERROR')


def get(http, route, event_id):
    response = http.get(route, query_string={'event_id': event_id})
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def assert_revenue(http, event_id, gross, net, fee, tickets):
    result = get(http, '/revenue', event_id)
    assert (result['totalGross'], result['totalNet'], result['paypalFees']) == (gross, net, fee)
    funnel = get(http, '/funnel', event_id)
    assert funnel['ticketsSold'] == tickets
    return funnel


def create_order(http, sample):
    response = http.post('/orders', json={'cart': [{'eventId': sample.event.id, 'participants': [
        {'name': m.name, 'surname': m.surname, 'email': m.email, 'phone': m.phone, 'birthdate': m.birthdate}
        for m in sample.people]}]})
    assert response.status_code == 201, response.get_json()
    return response.get_json()['id']


def scan_token(http, event_id):
    response = http.post('/scanner-token', json={'event_id': event_id})
    assert response.status_code == 201, response.get_json()
    return response.get_json()['token']


def test_group_checkout_capture_retry_and_snapshot_have_exact_totals(http, sample, gateway):
    """PAY-01/02/06, PAR-05, STA-02/04/13: 1 order != 2 tickets."""
    order_id = create_order(http, sample)
    assert list(db.collection('purchases').stream()) == []
    assert list(db.collection(f'participants/{sample.event.id}/participants_event').stream()) == []
    capture = http.post('/capture', json={'order_id': order_id})
    assert capture.status_code == 200, capture.get_json()
    purchase_id = capture.get_json()['purchase_id']
    assert_revenue(http, sample.event.id, 44, 42.5, 1.5, 2)
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 200
    assert retry.get_json()['purchase_id'] == purchase_id
    assert gateway.capture_calls == 1
    assert len(list(db.collection('purchases').stream())) == 1
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 2
    assert_revenue(http, sample.event.id, 44, 42.5, 1.5, 2)
    general = http.get('/general').get_json()
    assert general['total_purchases'] == 1
    assert general['total_gross_amount'] == '44.00'
    # No deployed triggers in this session: explicitly rebuild, then read via the handler.
    AnalyticsSnapshotService().rebuild_event_snapshot(sample.event.id)
    snapshot = get(http, '/snapshot', sample.event.id)
    assert snapshot['kpis']['participants'] == 2
    assert snapshot['kpis']['revenue_gross'] == 44
    assert snapshot['kpis']['revenue_net'] == 42.5


@pytest.mark.parametrize('state', INVALID_PURCHASE_STATES)
def test_status_changes_exclude_revenue_and_restore_without_deleting_participants(http, completed, state):
    """PAY-03/04/14, STA-05: all 6 invalid statuses via the admin API."""
    assert_revenue(http, completed.event.id, 44, 42.5, 1.5, 2)
    response = http.post('/purchase-status', json={'purchase_id': completed.purchase.id, 'status': state})
    assert response.status_code == 200, response.get_json()
    assert_revenue(http, completed.event.id, 0, 0, 0, 0)
    assert len(list(db.collection(f'participants/{completed.event.id}/participants_event').stream())) == 2
    assert http.get('/general').get_json()['total_purchases'] == 0
    AnalyticsSnapshotService().rebuild_event_snapshot(completed.event.id)
    assert get(http, '/snapshot', completed.event.id)['kpis']['revenue_gross'] == 0
    restored = http.post('/purchase-status', json={'purchase_id': completed.purchase.id, 'status': 'COMPLETED'})
    assert restored.status_code == 200
    assert_revenue(http, completed.event.id, 44, 42.5, 1.5, 2)


@pytest.mark.parametrize('state', INVALID_PURCHASE_STATES)
def test_capture_only_bad_state_characterizes_legacy_statistics_difference(http, completed, state):
    """PAY-03, STA-03, Q-04: characterization PASS does NOT resolve the discrepancy."""
    db.document('purchases/' + completed.purchase.id).update({'capture_status': state})
    assert_revenue(http, completed.event.id, 0, 0, 0, 0)
    legacy = http.get('/general').get_json()
    assert legacy['total_purchases'] == 1
    assert legacy['total_gross_amount'] == '44.00'
    assert len(list(db.collection(f'participants/{completed.event.id}/participants_event').stream())) == 2


@pytest.mark.parametrize('field', ['status', 'capture_status'])
def test_provider_rejection_does_not_create_purchase_or_participants(http, sample, gateway, field):
    """PAY-05: invalid provider completion, without calling an actual provider."""
    order_id = create_order(http, sample)
    gateway.bad_field, gateway.bad_state = field, 'DECLINED'
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 400, result.get_json()
    assert not list(db.collection('purchases').stream())
    assert not list(db.collection(f'participants/{sample.event.id}/participants_event').stream())
    assert db.document('orders/' + order_id).get().to_dict()['captured'] is False
    assert_revenue(http, sample.event.id, 0, 0, 0, 0)


def test_first_scan_duplicate_manual_entry_undo_and_reentry(http, completed):
    """QR-03/04/07, STA-10: +1,0,+1,-1,+1 entrances; revenues unchanged."""
    token = scan_token(http, completed.event.id)
    first = http.post('/scan', json={'scan_token': token, 'membership_id': completed.people[0].id})
    assert first.status_code == 200
    assert first.get_json()['result'] == 'valid'
    assert first.get_json()['entered_count'] == 1
    duplicate = http.post('/scan', json={'scan_token': token, 'membership_id': completed.people[0].id})
    assert duplicate.get_json()['result'] == 'already_scanned'
    assert duplicate.get_json()['entered_count'] == 1
    member = completed.people[1].id
    for entered, expected_result, count in [(True, 'entered', 2), (True, 'already_entered', 2),
                                            (False, 'undone', 1), (True, 'entered', 2)]:
        result = http.post('/manual-entry', json={'event_id': completed.event.id, 'membership_id': member, 'entered': entered})
        assert result.status_code == 200
        assert result.get_json()['result'] == expected_result
        assert result.get_json()['entered_count'] == count
    funnel = assert_revenue(http, completed.event.id, 44, 42.5, 1.5, 2)
    assert (funnel['enteredFlag'], funnel['scanned']) == (2, 2)
    assert funnel['showRatePct'] == 100
    assert len(list(db.collection(f'entrance_scans/{completed.event.id}/scans').stream())) == 2


@pytest.mark.parametrize('reason', ['token_missing', 'token_expired', 'token_inactive', 'member_missing', 'member_invalid', 'not_registered'])
def test_scan_rejections_never_create_an_entrance(http, completed, reason):
    """QR-02/05/06: HTTP 200 business rejections are not successful entrances."""
    token = scan_token(http, completed.event.id)
    member_id = completed.people[0].id
    expected = 'invalid_token'
    if reason == 'token_missing':
        token = 'missing'
    elif reason == 'token_expired':
        db.document('scan_tokens/' + token).update({'expires_at': completed.now - timedelta(seconds=1)})
    elif reason == 'token_inactive':
        db.document('scan_tokens/' + token).update({'is_active': False})
    elif reason == 'member_missing':
        member_id, expected = 'missing-synthetic-member', 'invalid_member_not_found'
    elif reason == 'member_invalid':
        db.document('memberships/' + member_id).update({'subscription_valid': False})
        expected = 'invalid_membership'
    elif reason == 'not_registered':
        db.document(f'participants/{completed.event.id}/participants_event/{member_id}').delete()
        expected = 'invalid_no_purchase'
    result = http.post('/scan', json={'scan_token': token, 'membership_id': member_id})
    assert result.status_code == 200
    assert result.get_json()['result'] == expected
    assert not list(db.collection(f'entrance_scans/{completed.event.id}/scans').stream())
    funnel = assert_revenue(http, completed.event.id, 44, 42.5, 1.5, 2)
    assert (funnel['enteredFlag'], funnel['scanned']) == (0, 0)


def test_zero_revenue_and_zero_capacity_do_not_produce_invalid_statistics(http, sample):
    """EVT-05, STA-07: empty event and denominator zero."""
    db.document('events/' + sample.event.id).update({'maxParticipants': 0})
    funnel = assert_revenue(http, sample.event.id, 0, 0, 0, 0)
    assert funnel['fillRatePct'] == funnel['showRatePct'] == funnel['scanCoveragePct'] == 0
    AnalyticsSnapshotService().rebuild_event_snapshot(sample.event.id)
    snapshot = get(http, '/snapshot', sample.event.id)
    assert snapshot['kpis']['avg_unit_payment'] == snapshot['kpis']['fill_rate'] == 0
