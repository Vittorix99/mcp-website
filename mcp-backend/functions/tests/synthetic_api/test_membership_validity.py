"""MEM-03/04: current canonical year AND valid flag, with no date fallback."""
from types import SimpleNamespace

import pytest

from config.firebase_config import db
from services.core.analytics_service import AnalyticsService
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from tests.synthetic_api.test_purchase_entrance_stats import create_order, order_payload, scan_token
from tests.synthetic_api.test_membership_discount_checkout import prepare_checkout


@pytest.mark.parametrize('has_year,flag,valid', [
    (True, True, True), (True, False, False),
    (False, True, False), (False, False, False),
])
def test_checkout_scanner_and_active_counts_use_the_same_rule(http, completed, gateway, has_year, flag, valid):
    case = completed
    member = case.people[0]
    db.document('memberships/' + member.id).update({
        'membership_years': [case.now.year] if has_year else [case.now.year - 1],
        'subscription_valid': flag, 'end_date': '31-12-2020',
    })
    db.document('events/' + case.event.id).update({
        'type': 'ONLY_ALREADY_REGISTERED_MEMBERS', 'allowDuplicates': True,
    })
    case.people = [member]
    order = http.post('/orders', json=order_payload(case))
    assert order.status_code == (201 if valid else 400), order.get_json()
    token = scan_token(http, case.event.id)
    scan = http.post('/scan', json={'scan_token': token, 'membership_id': member.id})
    assert scan.status_code == 200, scan.get_json()
    assert scan.get_json()['result'] == ('valid' if valid else 'invalid_membership')
    expected_active = 2 if valid else 1
    assert http.get('/general').get_json()['total_active_members'] == expected_active
    assert AnalyticsService().get_dashboard_kpis().members_count == expected_active
    assert AnalyticsService().get_membership_trend(case.now.year).total_active == expected_active
    snapshot = AnalyticsSnapshotService().rebuild_dashboard_snapshot()
    assert snapshot['kpis']['active_members'] == expected_active
    if not valid:
        assert gateway.create_calls == gateway.capture_calls == 0
        assert not list(db.collection(f'entrance_scans/{case.event.id}/scans').stream())


@pytest.mark.parametrize('mode', ['ONLY_MEMBERS', 'ONLY_ALREADY_REGISTERED_MEMBERS'])
def test_current_year_invalidated_member_cannot_pay_or_renew_automatically(http, sample, gateway, mode):
    member = sample.people[0]
    db.document('events/' + sample.event.id).update({'type': mode})
    db.document('membership_settings/price').set({'price_by_year': {str(sample.now.year): 5}})
    ref = db.document('memberships/' + member.id)
    ref.update({'subscription_valid': False})
    before = ref.get().to_dict()
    response = http.post('/orders', json=order_payload(SimpleNamespace(event=sample.event, people=[member])))
    assert response.status_code == 400, response.get_json()
    assert ref.get().to_dict() == before
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())


@pytest.mark.parametrize('mode', ['ONLY_MEMBERS', 'ONLY_ALREADY_REGISTERED_MEMBERS'])
@pytest.mark.parametrize('change', ['invalidated', 'year_removed'])
def test_membership_lost_after_order_creation_blocks_capture_before_provider(http, sample, gateway, mode, change):
    sample.people = sample.people[:1]
    db.document('events/' + sample.event.id).update({'type': mode})
    order_id = create_order(http, sample)
    ref = db.document('memberships/' + sample.people[0].id)
    ref.update({'subscription_valid': False} if change == 'invalidated' else {'membership_years': [sample.now.year - 1]})
    before = db.document('orders/' + order_id).get().to_dict()
    response = http.post('/capture', json={'order_id': order_id})
    assert response.status_code == 400, response.get_json()
    assert gateway.capture_calls == 0
    assert db.document('orders/' + order_id).get().to_dict() == before
    assert not list(db.collection('purchases').stream())


@pytest.mark.parametrize('flag', [True, False])
def test_previous_year_can_renew_and_then_pass_scanner(http, sample, gateway, flag):
    member, payload = prepare_checkout(sample, 'expired')
    db.document('memberships/' + member.id).update({'subscription_valid': flag})
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    gateway.capture_net = '20.50'
    captured = http.post('/capture', json={'order_id': order_id})
    assert captured.status_code == 200, captured.get_json()
    data = db.document('memberships/' + member.id).get().to_dict()
    assert data['subscription_valid'] is True
    assert data['membership_years'] == [sample.now.year - 1, sample.now.year]
    assert len([r for r in data['renewals'] if r['year'] == sample.now.year]) == 1
    token = scan_token(http, sample.event.id)
    scan = http.post('/scan', json={'scan_token': token, 'membership_id': member.id})
    assert scan.get_json()['result'] == 'valid'


def test_renewal_target_invalidated_after_someone_else_renewed_is_not_reactivated(http, sample, gateway):
    member, payload = prepare_checkout(sample, 'expired')
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    ref = db.document('memberships/' + member.id)
    ref.update({'membership_years': [sample.now.year - 1, sample.now.year], 'subscription_valid': False})
    before = ref.get().to_dict()
    gateway.capture_net = '20.50'
    captured = http.post('/capture', json={'order_id': order_id})
    assert captured.status_code == 400, captured.get_json()
    assert gateway.capture_calls == 0
    assert ref.get().to_dict() == before


@pytest.mark.parametrize('flag', [True, False])
def test_concurrent_renewal_during_provider_does_not_overwrite_membership(http, sample, gateway, monkeypatch, flag):
    member, payload = prepare_checkout(sample, 'expired')
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    ref = db.document('memberships/' + member.id)
    original = gateway.capture_order
    changed = {}
    def capture(target):
        result = original(target)
        ref.update({'membership_years': [sample.now.year - 1, sample.now.year],
                    'subscription_valid': flag, 'membership_type': 'manual'})
        changed.update(ref.get().to_dict())
        return result
    gateway.capture_net = '20.50'
    monkeypatch.setattr(gateway, 'capture_order', capture)
    captured = http.post('/capture', json={'order_id': order_id})
    assert captured.status_code == 409, captured.get_json()
    assert ref.get().to_dict() == changed
    stored = db.document('orders/' + order_id).get().to_dict()
    assert stored['captured'] is True and stored['orderStatus'] != 'COMPLETED'
    assert http.post('/capture', json={'order_id': order_id}).status_code == 409
    assert gateway.capture_calls == 1


@pytest.mark.parametrize('state', ['new', 'expired'])
def test_duplicate_people_provision_one_membership_and_both_tickets(http, sample, gateway, state):
    member, payload = prepare_checkout(sample, state)
    db.document('events/' + sample.event.id).update({'allowDuplicates': True})
    payload['cart'][0]['participants'].append(dict(payload['cart'][0]['participants'][0]))
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    captured = http.post('/capture', json={'order_id': order_id})
    assert captured.status_code == 200, captured.get_json()
    from google.cloud.firestore_v1 import FieldFilter
    matches = list(db.collection('memberships').where(filter=FieldFilter('email', '==', member.email)).stream())
    assert len(matches) == 1
    data = matches[0].to_dict()
    assert data['subscription_valid'] is True
    assert data['membership_years'].count(sample.now.year) == 1
    assert len([r for r in data['renewals'] if r['year'] == sample.now.year]) == 1
    people = list(db.collection(f'participants/{sample.event.id}/participants_event').stream())
    assert len(people) == 2
    assert all(person.to_dict()['membershipId'] == matches[0].id for person in people)
    assert db.document('orders/' + order_id).get().to_dict()['total'] == 44
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 200 and retry.get_json() == captured.get_json()
    assert gateway.capture_calls == 1


@pytest.mark.parametrize('mode', ['ONLY_MEMBERS', 'ONLY_ALREADY_REGISTERED_MEMBERS'])
def test_email_reassignment_cannot_validate_a_different_membership_before_capture(http, sample, gateway, mode):
    sample.people = sample.people[:1]
    db.document('events/' + sample.event.id).update({'type': mode})
    order_id = create_order(http, sample)
    original = db.document('memberships/' + sample.people[0].id)
    data = original.get().to_dict()
    original.update({'email': 'reassigned@example.com', 'subscription_valid': False})
    db.document('memberships/replacement-member').set(data)
    before = db.document('orders/' + order_id).get().to_dict()
    captured = http.post('/capture', json={'order_id': order_id})
    assert captured.status_code == 400, captured.get_json()
    assert gateway.capture_calls == 0
    assert db.document('orders/' + order_id).get().to_dict() == before
    assert not list(db.collection('purchases').stream())
