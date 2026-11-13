"""DIS-08: membership is included in event price, including when discounted.

Real HTTP handlers/repositories; fake PayPal and no deployed membership triggers.
The configured membership fee is recorded metadata, never a second charge.
"""
from types import SimpleNamespace

import pytest

from config.firebase_config import db
from models import DiscountCode, DiscountType, EventPurchaseAccessType, Membership
from services.payments.paypal_gateway import PayPalGatewayResponse
from tests.synthetic_api.test_concurrent_checkout import documents
from tests.synthetic_api.test_purchase_entrance_stats import assert_revenue, order_payload


SETTINGS_PATH = 'membership_settings/price'


def prepare_member(sample, state, member=None):
    member = member or sample.people[0]
    ref = db.document('memberships/' + member.id)
    if state == 'new':
        ref.delete()
    elif state == 'expired':
        previous = sample.now.year - 1
        start, end = f'{previous}-01-01T00:00:00+00:00', f'31-12-{previous}'
        ref.update({'membership_years': [previous], 'subscription_valid': False,
                    'start_date': start, 'end_date': end, 'membership_fee': 5,
                    'purchase_id': 'HISTORICAL', 'purchases': ['HISTORICAL'],
                    'renewals': [{'year': previous, 'start_date': start, 'end_date': end,
                                  'purchase_id': 'HISTORICAL', 'fee': 5}]})
    return member


def prepare_checkout(sample, state, discount=None, value=50, fee=2):
    db.document('events/' + sample.event.id).update({'type': EventPurchaseAccessType.ONLY_MEMBERS.value, 'fee': fee})
    db.document(SETTINGS_PATH).set({'price_by_year': {str(sample.now.year): 5}})
    person = prepare_member(sample, state)
    case = SimpleNamespace(event=sample.event, people=[person])
    payload = order_payload(case)
    if discount:
        code = DiscountCode(id='membership-discount', event_id=sample.event.id, code='INCLUDED',
                            discount_type=DiscountType(discount), discount_value=value,
                            max_uses=2, used_count=0, is_active=True)
        db.document('discount_codes/' + code.id).set(code.to_firestore())
        payload['cart'][0]['discountCode'] = code.code
    return person, payload


def create(http, payload):
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()['id']


def member_by_email(email):
    matches = [(key, value) for key, value in documents('memberships').items() if value.get('email') == email]
    assert len(matches) == 1, matches
    return matches[0]


def assert_membership(sample, person, state, purchase_id, before):
    identifier, member = member_by_email(person.email)
    if state != 'new':
        assert identifier == person.id
    else:
        assert identifier != person.id
    assert member['subscription_valid'] is True
    assert member['purchases'].count(purchase_id) == 1
    assert member['attended_events'].count(sample.event.id) == 1
    if state == 'current':
        for key in ('start_date', 'end_date', 'membership_years', 'renewals', 'membership_fee',
                    'membership_type', 'send_card_on_create'):
            assert member.get(key) == before[person.id].get(key), key
    else:
        assert member['membership_fee'] == 5
        assert member['send_card_on_create'] is True
        assert member['end_date'] == f'31-12-{sample.now.year}'
        renewal = [entry for entry in member['renewals'] if entry['year'] == sample.now.year]
        assert len(renewal) == 1
        assert renewal[0]['fee'] == 5 and renewal[0]['purchase_id'] == purchase_id
        assert len(member['renewals']) == (2 if state == 'expired' else 1)
        assert member['membership_years'] == ([sample.now.year - 1, sample.now.year] if state == 'expired' else [sample.now.year])
        if state == 'expired':
            old = [entry for entry in member['renewals'] if entry['year'] == sample.now.year - 1]
            assert old == before[person.id]['renewals']
            assert member['purchase_id'] == 'HISTORICAL'
            assert 'HISTORICAL' in member['purchases']
    return identifier


def persisted_checkout(sample):
    return {path: documents(path) for path in ('orders', 'memberships', 'purchases', 'discount_codes',
            f'participants/{sample.event.id}/participants_event',
            'discount_codes/membership-discount/reservation_receipts')}


@pytest.mark.parametrize('state', ['new', 'expired', 'current'])
@pytest.mark.parametrize('kind,value,fee,ticket,gross,net,provider_fee', [
    (None, 0, 0, 20, '20.00', '18.50', '1.50'),
    (None, 0, 2, 20, '22.00', '20.50', '1.50'),
    ('PERCENTAGE', 50, 0, 10, '10.00', '8.50', '1.50'),
    ('PERCENTAGE', 50, 2, 10, '12.00', '10.50', '1.50'),
    ('FIXED', 5, 0, 15, '15.00', '13.50', '1.50'),
    ('FIXED', 5, 2, 15, '17.00', '15.50', '1.50'),
    ('FIXED_PRICE', 10, 0, 10, '10.00', '8.50', '1.50'),
    ('FIXED_PRICE', 10, 2, 10, '12.00', '10.50', '1.50'),
    ('PERCENTAGE', 100, 0, 0, '0.00', '0.00', '0.00'),
    ('PERCENTAGE', 100, 2, 0, '2.00', '0.50', '1.50'),
])
def test_included_membership_checkout_formula_and_completed_retry(
        http, sample, gateway, state, kind, value, fee, ticket, gross, net, provider_fee):
    person, payload = prepare_checkout(sample, state, kind, value, fee)
    before = documents('memberships')
    assert http.get('/general').get_json()['total_active_members'] == (2 if state == 'current' else 1)
    order_id = create(http, payload)
    stored = db.document('orders/' + order_id).get().to_dict()
    assert stored['total'] == float(gross)
    assert len(stored['membershipTargets']) == (0 if state == 'current' else 1)
    assert stored['membershipFee'] == (None if state == 'current' else 5)
    assert documents('memberships') == before
    assert gateway.create_calls == 1 and gateway.capture_calls == 0
    assert not documents('purchases')
    if kind:
        assert db.document('discount_codes/membership-discount').get().to_dict()['usedCount'] == 0
    gateway.capture_net, gateway.capture_fee = net, provider_fee
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    purchase_id = result.get_json()['purchase_id']
    purchase = documents('purchases')[purchase_id]
    assert purchase['amount_total'] == gross
    assert purchase['net_amount'] == net and purchase['paypal_fee'] == provider_fee
    assert purchase['participants_count'] == 1
    identifier = assert_membership(sample, person, state, purchase_id, before)
    assert purchase['membership_ids'] == [identifier]
    people = documents(f'participants/{sample.event.id}/participants_event')
    assert len(people) == 1
    participant = next(iter(people.values()))
    assert participant['membershipId'] == identifier and participant['membership_included'] is True
    assert participant['price'] == ticket and participant['purchase_id'] == purchase_id
    assert len(documents('memberships')) == 2
    assert http.get('/general').get_json()['total_active_members'] == 2
    if kind:
        assert db.document('discount_codes/membership-discount').get().to_dict()['usedCount'] == 1
    assert_revenue(http, sample.event.id, float(gross), float(net), float(provider_fee), 1)
    completed = persisted_checkout(sample)
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 200 and retry.get_json()['purchase_id'] == purchase_id
    assert gateway.capture_calls == 1
    assert persisted_checkout(sample) == completed


def test_mixed_group_includes_only_required_memberships_without_extra_charge(http, sample, gateway):
    db.document('events/' + sample.event.id).update({'type': EventPurchaseAccessType.ONLY_MEMBERS.value})
    db.document(SETTINGS_PATH).set({'price_by_year': {str(sample.now.year): 5}})
    current, expired = sample.people
    prepare_member(sample, 'expired', expired)
    new = Membership(id='never-persisted', name='Giulia', surname='Prova', email='new-group@example.com',
                     phone='+999000003', birthdate='10-01-1985')
    before = documents('memberships')
    order_id = create(http, order_payload(SimpleNamespace(event=sample.event, people=[current, expired, new])))
    order = db.document('orders/' + order_id).get().to_dict()
    assert order['total'] == 66 and order['membershipFee'] == 5
    assert len(order['membershipTargets']) == 2
    assert documents('memberships') == before
    gateway.capture_net = '64.50'
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    purchase_id = result.get_json()['purchase_id']
    identifiers = {assert_membership(sample, person, state, purchase_id, before)
                   for person, state in [(current, 'current'), (expired, 'expired'), (new, 'new')]}
    purchase = documents('purchases')[purchase_id]
    assert purchase['amount_total'] == '66.00' and purchase['participants_count'] == 3
    assert set(purchase['membership_ids']) == identifiers
    assert len(documents('memberships')) == 3
    assert http.get('/general').get_json()['total_active_members'] == 3
    assert len(documents(f'participants/{sample.event.id}/participants_event')) == 3
    assert_revenue(http, sample.event.id, 66, 64.5, 1.5, 3)
    completed = persisted_checkout(sample)
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 200 and retry.get_json()['purchase_id'] == purchase_id
    assert gateway.capture_calls == 1 and persisted_checkout(sample) == completed


@pytest.mark.parametrize('state', ['new', 'expired'])
@pytest.mark.parametrize('discount', [False, True])
@pytest.mark.parametrize('failure', ['http', 'declined'])
def test_failed_payment_never_creates_or_renews_membership(http, sample, gateway, state, discount, failure):
    _, payload = prepare_checkout(sample, state, 'PERCENTAGE' if discount else None)
    before = documents('memberships')
    order_id = create(http, payload)
    if failure == 'http':
        gateway.capture_result = PayPalGatewayResponse(503, {'error': 'Synthetic unavailable'})
    else:
        gateway.bad_field, gateway.bad_state = 'capture_status', 'DECLINED'
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == (502 if failure == 'http' else 400), result.get_json()
    assert documents('memberships') == before
    assert not documents('purchases')
    assert not documents(f'participants/{sample.event.id}/participants_event')
    assert db.document('orders/' + order_id).get().to_dict()['captured'] is False
    assert gateway.create_calls == gateway.capture_calls == 1
    if discount:
        code = db.document('discount_codes/membership-discount').get().to_dict()
        assert code['usedCount'] == 0
        assert bool(code['reservations']) == (failure == 'http')
    assert_revenue(http, sample.event.id, 0, 0, 0, 0)


@pytest.mark.parametrize('state', ['new', 'expired'])
@pytest.mark.parametrize('discount', [False, True])
@pytest.mark.parametrize('setting', ['missing', 'invalid'])
def test_target_without_usable_fee_setting_is_rejected_before_provider(http, sample, gateway, state, discount, setting):
    _, payload = prepare_checkout(sample, state, 'PERCENTAGE' if discount else None)
    if setting == 'missing':
        db.document(SETTINGS_PATH).delete()
    else:
        db.document(SETTINGS_PATH).set({'price_by_year': {str(sample.now.year): 'invalid'}})
    before = persisted_checkout(sample)
    result = http.post('/orders', json=payload)
    assert result.status_code == 400, result.get_json()
    assert gateway.create_calls == gateway.capture_calls == 0
    assert persisted_checkout(sample) == before


@pytest.mark.parametrize('discount', [False, True])
def test_current_member_needs_no_membership_fee_setting(http, sample, gateway, discount):
    person, payload = prepare_checkout(sample, 'current', 'PERCENTAGE' if discount else None)
    before = documents('memberships')
    db.document(SETTINGS_PATH).delete()
    order_id = create(http, payload)
    order = db.document('orders/' + order_id).get().to_dict()
    assert order['membershipTargets'] == [] and order['membershipFee'] is None
    assert order['total'] == (12 if discount else 22)
    assert gateway.create_calls == 1 and gateway.capture_calls == 0

    gateway.capture_net = '10.50' if discount else '20.50'
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    assert_membership(sample, person, 'current', result.get_json()['purchase_id'], before)
    assert_revenue(http, sample.event.id, 12 if discount else 22,
                   10.5 if discount else 20.5, 1.5, 1)


@pytest.mark.parametrize('state', ['new', 'expired'])
def test_capture_uses_fee_staged_at_create_even_if_settings_change(http, sample, gateway, state):
    person, payload = prepare_checkout(sample, state, 'PERCENTAGE')
    before = documents('memberships')
    order_id = create(http, payload)
    db.document(SETTINGS_PATH).set({'price_by_year': {str(sample.now.year): 9}})
    gateway.capture_net = '10.50'
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    assert_membership(sample, person, state, result.get_json()['purchase_id'], before)
    assert db.document('orders/' + order_id).get().to_dict()['total'] == 12
    assert_revenue(http, sample.event.id, 12, 10.5, 1.5, 1)


def test_group_discount_rejection_never_provisions_included_membership(http, sample, gateway):
    _, payload = prepare_checkout(sample, 'new', 'PERCENTAGE')
    payload['cart'][0]['participants'].append(order_payload(sample)['cart'][0]['participants'][1])
    before = persisted_checkout(sample)
    result = http.post('/orders', json=payload)
    assert result.status_code == 400, result.get_json()
    assert gateway.create_calls == gateway.capture_calls == 0
    assert persisted_checkout(sample) == before
