"""Admin recovery with real emulator repositories and a read-only fake provider."""
from copy import deepcopy
from threading import Barrier, Event, Lock

import pytest

from api.public import event_payment_api
from config.firebase_config import db
from errors.service_errors import ExternalServiceError
from models import DiscountCode, DiscountType
from services.payments.paypal_gateway import PayPalGatewayResponse
from tests.synthetic_api.test_concurrent_checkout import concurrent_captures, documents
from tests.synthetic_api.test_purchase_entrance_stats import assert_revenue, order_payload


def create_checkout_order(http, sample, gateway, discount=False):
    if discount:
        sample.people = sample.people[:1]
        code = DiscountCode(id='recovery-discount', event_id=sample.event.id, code='RECOVER',
                            discount_type=DiscountType.PERCENTAGE, discount_value=50,
                            max_uses=1, used_count=0, is_active=True)
        db.document('discount_codes/' + code.id).set(code.to_firestore())
        gateway.capture_net = '10.50'
    payload = order_payload(sample)
    if discount:
        payload['cart'][0]['discountCode'] = 'RECOVER'
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()['id']


def pending_order(http, sample, gateway, monkeypatch, stage='save_purchase', discount=False):
    order_id = create_checkout_order(http, sample, gateway, discount)
    payments = event_payment_api.event_payment_service
    if stage == 'provider_response':
        owner, name = gateway, 'capture_order'
    elif stage == 'set_purchase_id':
        owner, name = payments.order_repository, stage
    elif stage == 'participant_created':
        owner, name = payments.participant_repository, 'create_for_purchase'
    else:
        owner, name = payments, stage
    original = getattr(owner, name)

    def fail(*args, **kwargs):
        if stage in ('provider_response', 'participant_created'):
            original(*args, **kwargs)
        if stage == 'provider_response':
            raise ExternalServiceError('Lost response after provider capture')
        raise RuntimeError('Interrupted local provisioning')

    with monkeypatch.context() as patch:
        patch.setattr(owner, name, fail)
        result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == (502 if stage == 'provider_response' else 500), result.get_json()
    return order_id


def assert_recovered(http, sample, gateway, order_id, discount=False):
    orders = documents('orders')
    purchases = documents('purchases')
    people = documents(f'participants/{sample.event.id}/participants_event')
    assert len(purchases) == 1 and len(people) == len(sample.people)
    purchase_id = next(iter(purchases))
    assert orders[order_id]['captured'] is True
    assert orders[order_id]['orderStatus'] == 'COMPLETED'
    assert orders[order_id]['purchase_id'] == purchase_id
    assert {p['purchase_id'] for p in people.values()} == {purchase_id}
    assert gateway.capture_calls == 1
    for member in sample.people:
        data = db.document('memberships/' + member.id).get().to_dict()
        assert data['purchases'].count(purchase_id) == 1
        assert data['attended_events'].count(sample.event.id) == 1
    if discount:
        code = db.document('discount_codes/recovery-discount').get().to_dict()
        assert code['usedCount'] == 1 and code['reservations'] == {}
    assert_revenue(http, sample.event.id, 12 if discount else 44,
                   10.5 if discount else 42.5, 1.5, len(sample.people))
    return purchase_id


@pytest.mark.parametrize('stage', ['save_purchase', 'set_purchase_id', 'handle_event_participants',
                                   'participant_created', 'provider_response'])
@pytest.mark.parametrize('discount', [False, True])
def test_admin_recovers_each_interruption_without_new_capture_or_duplicates(
        http, sample, gateway, monkeypatch, stage, discount):
    order_id = pending_order(http, sample, gateway, monkeypatch, stage, discount)
    response = http.post('/recover-order', json={'order_id': order_id}, headers={'Authorization': 'Bearer test'})
    assert response.status_code == 200, response.get_json()
    purchase_id = assert_recovered(http, sample, gateway, order_id, discount)
    before = documents('purchases')
    for route in ('/recover-order', '/capture'):
        retry = http.post(route, json={'order_id': order_id}, headers={'Authorization': 'Bearer test'})
        assert retry.status_code == 200 and retry.get_json()['purchase_id'] == purchase_id
    assert documents('purchases') == before
    assert_recovered(http, sample, gateway, order_id, discount)


@pytest.mark.parametrize('discount', [False, True])
@pytest.mark.parametrize('stage', ['save_purchase', 'participant_created'])
def test_two_admin_recoveries_reuse_partial_participant_without_resetting_flags(
        http, sample, gateway, monkeypatch, stage, discount):
    order_id = pending_order(http, sample, gateway, monkeypatch, stage, discount)
    path = f'participants/{sample.event.id}/participants_event'
    existing_id = next(iter(documents(path)), None)
    if existing_id:
        db.document(path + '/' + existing_id).update({'ticket_sent': True, 'entered': True})
    repo = event_payment_api.event_payment_service.purchase_repository
    original = repo.find_by_order
    barrier = Barrier(2, timeout=10)
    lock = Lock()
    reads = 0

    def overlap(target):
        nonlocal reads
        result = original(target)
        with lock:
            reads += 1
            wait = reads <= 2
        if wait:
            barrier.wait()
        return result

    with monkeypatch.context() as patch:
        patch.setattr(repo, 'find_by_order', overlap)
        results = concurrent_captures(http, [order_id, order_id], ['/recover-order'] * 2)
    assert [status for status, _ in results] == [200, 200], results
    assert results[0][1]['purchase_id'] == results[1][1]['purchase_id']
    assert_recovered(http, sample, gateway, order_id, discount)
    if existing_id:
        existing = db.document(path + '/' + existing_id).get().to_dict()
        assert existing['entered'] is True and existing['ticket_sent'] is True


@pytest.mark.parametrize('discount', [False, True])
def test_recovery_and_original_checkout_share_purchase_and_participant_ids(
        http, sample, gateway, monkeypatch, discount):
    order_id = create_checkout_order(http, sample, gateway, discount)
    payments = event_payment_api.event_payment_service
    original_save = payments.save_purchase
    original_get = gateway.get_order
    checkout_paused, resume_checkout = Event(), Event()
    lock = Lock()
    first = True

    def overlap_save(*args, **kwargs):
        nonlocal first
        with lock:
            is_checkout = first
            first = False
        if is_checkout:
            checkout_paused.set()
            assert resume_checkout.wait(timeout=10)
            return original_save(*args, **kwargs)
        try:
            return original_save(*args, **kwargs)
        finally:
            resume_checkout.set()

    def verified_read(order_id):
        assert checkout_paused.wait(timeout=10)
        return original_get(order_id)

    with monkeypatch.context() as patch:
        patch.setattr(payments, 'save_purchase', overlap_save)
        patch.setattr(gateway, 'get_order', verified_read)
        results = concurrent_captures(http, [order_id, order_id], ['/capture', '/recover-order'])
    assert [status for status, _ in results] == [200, 200], results
    assert_recovered(http, sample, gateway, order_id, discount)


@pytest.mark.parametrize('problem', ['pending', 'wrong_order', 'wrong_currency', 'wrong_amount',
                                    'membership', 'legacy_discount', 'duplicate_purchase'])
def test_unverifiable_recovery_keeps_persisted_state_unchanged(
        http, sample, gateway, monkeypatch, problem):
    discount = problem == 'legacy_discount'
    stage = 'handle_event_participants' if problem == 'duplicate_purchase' else 'save_purchase'
    order_id = pending_order(http, sample, gateway, monkeypatch, stage, discount)
    if problem == 'membership':
        db.document('orders/' + order_id).update({'membershipTargets': order_payload(sample)['cart'][0]['participants']})
    elif problem == 'legacy_discount':
        db.document(f'discount_codes/recovery-discount/reservation_receipts/{order_id}').delete()
    elif problem == 'duplicate_purchase':
        purchase = next(iter(documents('purchases').values()))
        db.document('purchases/duplicate').set(purchase)
    else:
        body = deepcopy(gateway.get_order(order_id).payload)
        if problem == 'pending':
            body['status'] = 'PENDING'
        elif problem == 'wrong_order':
            body['id'] = 'OTHER'
        elif problem == 'wrong_currency':
            body['purchase_units'][0]['payments']['captures'][0]['amount']['currency_code'] = 'USD'
        else:
            body['purchase_units'][0]['payments']['captures'][0]['amount']['value'] = '1.00'
        gateway.read_result = PayPalGatewayResponse(200, body)
    before = {name: documents(name) for name in ('orders', 'purchases', 'discount_codes', 'memberships')}
    result = http.post('/recover-order', json={'order_id': order_id}, headers={'Authorization': 'Bearer test'})
    assert result.status_code == 409, result.get_json()
    assert {name: documents(name) for name in before} == before
    assert not documents(f'participants/{sample.event.id}/participants_event')
    assert gateway.capture_calls == 1


def test_recovery_keeps_unique_legacy_purchase_and_participant_ids(http, sample, gateway, monkeypatch):
    order_id = pending_order(http, sample, gateway, monkeypatch, 'participant_created')
    purchase_id, purchase = next(iter(documents('purchases').items()))
    db.document('purchases/legacy-purchase').set(purchase)
    db.document('purchases/' + purchase_id).delete()
    db.document('orders/' + order_id).update({'purchase_id': 'legacy-purchase'})
    path = f'participants/{sample.event.id}/participants_event'
    participant_id, person = next(iter(documents(path).items()))
    person.pop('checkoutIndex', None)
    person['purchase_id'] = 'legacy-purchase'
    person['ticket_sent'] = True
    db.document(path + '/legacy-person').set(person)
    db.document(path + '/' + participant_id).delete()
    result = http.post('/recover-order', json={'order_id': order_id}, headers={'Authorization': 'Bearer test'})
    assert result.status_code == 200, result.get_json()
    assert result.get_json()['purchase_id'] == 'legacy-purchase'
    assert set(documents('purchases')) == {'legacy-purchase'}
    assert len(documents(path)) == 2
    assert documents(path)['legacy-person']['ticket_sent'] is True
    assert gateway.capture_calls == 1


def test_checkout_still_allows_duplicate_people_when_event_permits_it(http, sample, gateway):
    db.document('events/' + sample.event.id).update({'allowDuplicates': True})
    payload = order_payload(sample)
    payload['cart'][0]['participants'] = [payload['cart'][0]['participants'][0]] * 2
    created = http.post('/orders', json=payload)
    assert created.status_code == 201, created.get_json()
    response = http.post('/capture', json={'order_id': created.get_json()['id']})
    assert response.status_code == 200, response.get_json()
    assert len(documents(f'participants/{sample.event.id}/participants_event')) == 2
    assert_revenue(http, sample.event.id, 44, 42.5, 1.5, 2)


@pytest.mark.parametrize('problem', ['unrelated_member', 'malformed_participant', 'malformed_lookup',
                                    'price_nan', 'price_infinity', 'discount_exceeds_price',
                                    'legacy_timestamp', 'legacy_payer', 'legacy_payment_method',
                                    'ticket_position'])
def test_integrity_conflicts_return_409_without_any_persisted_changes(
        http, sample, gateway, monkeypatch, problem):
    import json
    from models import Membership

    stage = ('participant_created' if problem == 'ticket_position' else
             'handle_event_participants' if problem.startswith('legacy_') else 'save_purchase')
    order_id = pending_order(http, sample, gateway, monkeypatch, stage,
                             discount=problem == 'discount_exceeds_price')
    ref = db.document('orders/' + order_id)
    data = ref.get().to_dict()
    if problem == 'unrelated_member':
        extra = Membership(id='unrelated-member', email='extra@example.test')
        db.document('memberships/' + extra.id).set(extra.to_firestore())
        data['membershipLookup']['extra@example.test'] = {**extra.to_firestore(), 'id': extra.id}
        ref.update({'membershipLookup': data['membershipLookup']})
    elif problem == 'malformed_participant':
        ref.update({'participants': data['participants'] + [None]})
    elif problem == 'malformed_lookup':
        data['membershipLookup'][sample.people[0].email] = None
        ref.update({'membershipLookup': data['membershipLookup']})
    elif problem in ('price_nan', 'price_infinity'):
        ref.update({'eventPrice': float('nan') if problem == 'price_nan' else float('inf')})
    elif problem == 'discount_exceeds_price':
        ref.update({'discountAmount': 21})
    elif problem == 'ticket_position':
        path = f'participants/{sample.event.id}/participants_event'
        db.document(path + '/' + next(iter(documents(path)))).update({'checkoutIndex': 99})
    else:
        purchase_id = next(iter(documents('purchases')))
        changes = ({'timestamp': '2020-01-01T12:00:00Z'} if problem == 'legacy_timestamp' else
                   {'payer_email': 'different@example.test'} if problem == 'legacy_payer' else
                   {'payment_method': 'apple_pay'})
        db.document('purchases/' + purchase_id).update(changes)

    paths = ['orders', 'purchases', 'memberships', 'discount_codes',
             f'participants/{sample.event.id}/participants_event',
             'discount_codes/recovery-discount/reservation_receipts']
    # Canonical snapshots preserve equality even for Firestore NaN values.
    def snapshot():
        return json.dumps({path: documents(path) for path in paths}, sort_keys=True, default=str)
    before = snapshot()
    response = http.post('/recover-order', json={'order_id': order_id}, headers={'Authorization': 'Bearer test'})
    assert response.status_code == 409, response.get_json()
    assert snapshot() == before
    assert gateway.capture_calls == 1
