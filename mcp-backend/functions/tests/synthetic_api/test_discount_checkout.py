"""Discount matrix slice: actual handlers/repositories, fake PayPal, no triggers."""
import pytest

from api.public import event_payment_api
from config.firebase_config import db
from errors.service_errors import ConflictError
from models import DiscountCode, DiscountType
from services.payments.paypal_gateway import PayPalGatewayResponse
from tests.synthetic_api.test_purchase_entrance_stats import assert_revenue, order_payload


@pytest.fixture
def discount_case(sample):
    sample.people = sample.people[:1]
    code = DiscountCode(id='case-discount', event_id=sample.event.id, code='MCP50',
                        discount_type=DiscountType.PERCENTAGE, discount_value=50,
                        max_uses=2, used_count=0, is_active=True)
    sample.discount_ref = db.document('discount_codes/' + code.id)
    sample.discount_ref.set(code.to_firestore())
    return sample


def checkout_payload(case):
    payload = order_payload(case)
    payload['cart'][0]['discountCode'] = ' mcp50 '
    return payload


def validate_discount(http, case):
    response = http.post('/discount-validation', json={
        'eventId': case.event.id, 'code': ' mcp50 ',
        'participantsCount': len(case.people), 'payerEmail': case.people[0].email.upper(),
    })
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def assert_no_provisioning(http, case):
    assert not list(db.collection('purchases').stream())
    assert not list(db.collection(f'participants/{case.event.id}/participants_event').stream())
    assert not list(db.collection(f'entrance_scans/{case.event.id}/scans').stream())
    assert_revenue(http, case.event.id, 0, 0, 0, 0)


@pytest.mark.parametrize('kind,value,price,discount,final,gross,net', [
    ('PERCENTAGE', 50, 20, 10, 10, '12.00', '10.50'),
    ('FIXED', 5, 20, 5, 15, '17.00', '15.50'),
    ('FIXED_PRICE', 10, 25, 15, 10, '12.00', '10.50'),
    ('PERCENTAGE', 100, 20, 20, 0, '2.00', '0.50'),
    ('FIXED', 20, 20, 20, 0, '2.00', '0.50'),
    ('FIXED_PRICE', 0, 20, 20, 0, '2.00', '0.50'),
    ('FIXED_PRICE', 20, 20, 0, 20, '22.00', '20.50'),
])
def test_discount_formula_capture_and_retry_use_exact_totals(
        http, discount_case, gateway, kind, value, price, discount, final, gross, net):
    """DIS-01/02/03/07: normalization, separate event fee, one usage despite retry."""
    case = discount_case
    db.document('events/' + case.event.id).update({'price': price})
    case.discount_ref.update({'discountType': kind, 'discountValue': value})
    before = case.discount_ref.get().to_dict()
    validation = validate_discount(http, case)
    assert validation['valid'] is True
    assert (validation['discount_amount'], validation['final_price']) == (discount, final)
    assert case.discount_ref.get().to_dict() == before
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    order = db.document('orders/' + order_id).get().to_dict()
    assert order['total'] == float(gross)
    assert order['discountCodeId'] == case.discount_ref.id
    assert order['discountCode'] == 'MCP50'
    assert order['discountAmount'] == discount
    assert order['originalPrice'] == price
    assert case.discount_ref.get().to_dict() == before
    assert_no_provisioning(http, case)
    # Preserve the amount requested by the service; override only the fake fee breakdown.
    gateway.capture_net = net
    capture = http.post('/capture', json={'order_id': order_id})
    assert capture.status_code == 200, capture.get_json()
    purchase_id = capture.get_json()['purchase_id']
    purchase = db.document('purchases/' + purchase_id).get().to_dict()
    assert purchase['discountCodeId'] == case.discount_ref.id
    assert purchase['discountAmount'] == discount
    participants = list(db.collection(f'participants/{case.event.id}/participants_event').stream())
    assert len(participants) == 1
    participant = participants[0].to_dict()
    assert participant['purchase_id'] == purchase_id
    assert participant['price'] == final
    assert participant['priceOriginal'] == price
    assert participant['discountCodeId'] == case.discount_ref.id
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert_revenue(http, case.event.id, float(gross), float(net), 1.5, 1)
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 200
    assert retry.get_json()['purchase_id'] == purchase_id
    assert gateway.create_calls == gateway.capture_calls == 1
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert len(list(db.collection('purchases').stream())) == 1
    assert len(list(db.collection(f'participants/{case.event.id}/participants_event').stream())) == 1
    assert_revenue(http, case.event.id, float(gross), float(net), 1.5, 1)


@pytest.mark.parametrize('reason', ['missing', 'inactive', 'exhausted', 'other_event'])
def test_unavailable_discount_rejected_before_provider_without_writes(http, discount_case, gateway, reason):
    """DIS-03: lookup/availability failures do not create orders or consume usages."""
    case = discount_case
    if reason == 'missing':
        case.discount_ref.delete()
    else:
        changes = {'inactive': {'isActive': False}, 'exhausted': {'usedCount': 2},
                   'other_event': {'event_id': 'different-synthetic-event'}}
        case.discount_ref.update(changes[reason])
    before = case.discount_ref.get().to_dict()
    assert validate_discount(http, case)['valid'] is False
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 400, response.get_json()
    assert case.discount_ref.get().to_dict() == before
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
    assert_no_provisioning(http, case)


@pytest.mark.parametrize('restriction,allowed', [
    ('email_match', True), ('email_other', False), ('member_match', True),
    ('member_other', False), ('member_missing', False),
])
def test_personal_discount_checks_recipient_in_validation_and_checkout(
        http, discount_case, gateway, restriction, allowed):
    """DIS-05: restrictions refer to checkout participant identity, not fake PayPal payer."""
    case = discount_case
    if restriction.startswith('email'):
        email = case.people[0].email.upper() if allowed else 'other@example.com'
        case.discount_ref.update({'restrictedEmail': email})
    else:
        member_id = {'member_match': case.people[0].id,
                     'member_other': 'case-member-b', 'member_missing': 'missing-member'}[restriction]
        case.discount_ref.update({'restrictedMembershipId': member_id})
    before = case.discount_ref.get().to_dict()
    assert validate_discount(http, case)['valid'] is allowed
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == (201 if allowed else 400), response.get_json()
    assert gateway.create_calls == (1 if allowed else 0)
    assert gateway.capture_calls == 0
    assert len(list(db.collection('orders').stream())) == (1 if allowed else 0)
    assert case.discount_ref.get().to_dict() == before
    assert_no_provisioning(http, case)


def test_group_discount_is_rejected_without_provider_or_usage(http, sample, gateway):
    """DIS-04: a valid code is still restricted to one checkout participant."""
    code = DiscountCode(id='case-discount', event_id=sample.event.id, code='MCP50',
                        discount_type=DiscountType.PERCENTAGE, discount_value=50, max_uses=2)
    sample.discount_ref = db.document('discount_codes/' + code.id)
    sample.discount_ref.set(code.to_firestore())
    before = sample.discount_ref.get().to_dict()
    assert validate_discount(http, sample)['valid'] is False
    response = http.post('/orders', json=checkout_payload(sample))
    assert response.status_code == 400, response.get_json()
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
    assert sample.discount_ref.get().to_dict() == before
    assert_no_provisioning(http, sample)


@pytest.mark.parametrize('failure', ['http_error', 'declined'])
def test_failed_capture_does_not_consume_discount(http, discount_case, gateway, failure):
    """DIS-07: release only a known failure; retain ambiguous provider outcomes."""
    case = discount_case
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    before = case.discount_ref.get().to_dict()
    if failure == 'http_error':
        gateway.capture_result = PayPalGatewayResponse(503, {'error': 'Synthetic unavailable'})
    else:
        gateway.bad_field, gateway.bad_state = 'capture_status', 'DECLINED'
    capture = http.post('/capture', json={'order_id': order_id})
    assert capture.status_code == (502 if failure == 'http_error' else 400), capture.get_json()
    assert gateway.create_calls == gateway.capture_calls == 1
    assert db.document('orders/' + order_id).get().to_dict()['captured'] is False
    after = case.discount_ref.get().to_dict()
    assert after['usedCount'] == before['usedCount']
    if failure == 'http_error':
        assert after['reservations'][order_id]['state'] == 'capturing'
    else:
        assert after['reservations'] == {}
    assert_no_provisioning(http, case)


def test_failure_after_discount_claim_retains_usage_and_retry_does_not_claim_again(
        http, discount_case, gateway, monkeypatch):
    """DIS-07: no imaginary rollback after a successful capture and usage claim."""
    case = discount_case
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    gateway.capture_net = '10.50'

    def fail_after_claim(*args, **kwargs):
        raise RuntimeError('Synthetic failure after discount claim')

    with monkeypatch.context() as patch:
        patch.setattr(event_payment_api.event_payment_service, 'save_purchase', fail_after_claim)
        capture = http.post('/capture', json={'order_id': order_id})
    assert capture.status_code == 500, capture.get_json()
    order = db.document('orders/' + order_id).get().to_dict()
    assert order['captured'] is True
    assert order['orderStatus'] == 'PAYMENT_CAPTURED'
    assert not order.get('purchase_id')
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert_no_provisioning(http, case)
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 409, retry.get_json()
    assert retry.get_json()['code'] == 'ORDER_PROVISIONING_INCOMPLETE'
    assert gateway.capture_calls == 1
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert db.document('orders/' + order_id).get().to_dict() == order
    assert_no_provisioning(http, case)


@pytest.mark.parametrize('kind,value', [
    ('PERCENTAGE', -0.01), ('PERCENTAGE', 0), ('PERCENTAGE', 100.01),
    ('FIXED', -0.01), ('FIXED', 0), ('FIXED', 20.01),
    ('FIXED_PRICE', -0.01), ('FIXED_PRICE', 20.01),
])
def test_invalid_discount_amount_rejected_without_provider_or_writes(
        http, discount_case, gateway, kind, value):
    """DIS-02: invalid limits against a 20.00 ticket never reach PayPal."""
    case = discount_case
    case.discount_ref.update({'discountType': kind, 'discountValue': value})
    before = case.discount_ref.get().to_dict()
    validation = validate_discount(http, case)
    assert validation['valid'] is False
    assert validation['error_message'] == 'Codice sconto non valido per questo importo'
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 400, response.get_json()
    assert response.get_json()['error'] == 'Codice sconto non valido per questo importo'
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
    assert case.discount_ref.get().to_dict() == before
    assert_no_provisioning(http, case)


def test_zero_total_checkout_characterizes_fake_provider_path(http, discount_case, gateway):
    """DIS-02 characterization: fake acceptance does not prove live zero-value checkout."""
    case = discount_case
    db.document('events/' + case.event.id).update({'fee': 0})
    case.discount_ref.update({'discountValue': 100})
    validation = validate_discount(http, case)
    assert validation['valid'] is True
    assert (validation['discount_amount'], validation['final_price']) == (20, 0)
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    assert db.document('orders/' + order_id).get().to_dict()['total'] == 0
    assert case.discount_ref.get().to_dict()['usedCount'] == 0
    assert_no_provisioning(http, case)
    gateway.capture_fee, gateway.capture_net = '0.00', '0.00'
    capture = http.post('/capture', json={'order_id': order_id})
    assert capture.status_code == 200, capture.get_json()
    purchase_id = capture.get_json()['purchase_id']
    purchase = db.document('purchases/' + purchase_id).get().to_dict()
    assert purchase['amount_total'] == '0.00'
    assert purchase['paypal_fee'] == purchase['net_amount'] == '0.00'
    participants = list(db.collection(f'participants/{case.event.id}/participants_event').stream())
    assert len(participants) == 1
    assert participants[0].to_dict()['price'] == 0
    assert participants[0].to_dict()['purchase_id'] == purchase_id
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert_revenue(http, case.event.id, 0, 0, 0, 1)
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 200
    assert retry.get_json()['purchase_id'] == purchase_id
    assert gateway.create_calls == gateway.capture_calls == 1
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert len(list(db.collection('purchases').stream())) == 1
    assert len(list(db.collection(f'participants/{case.event.id}/participants_event').stream())) == 1
    assert_revenue(http, case.event.id, 0, 0, 0, 1)


def test_declined_payment_releases_last_slot_for_another_order(http, discount_case, gateway):
    case = discount_case
    case.discount_ref.update({'maxUses': 1})
    order_ids = []
    for _ in range(2):
        response = http.post('/orders', json=checkout_payload(case))
        assert response.status_code == 201, response.get_json()
        order_ids.append(response.get_json()['id'])
    gateway.bad_field, gateway.bad_state = 'capture_status', 'DECLINED'
    rejected = http.post('/capture', json={'order_id': order_ids[0]})
    assert rejected.status_code == 400, rejected.get_json()
    assert case.discount_ref.get().to_dict()['reservations'] == {}
    gateway.bad_field = gateway.bad_state = None
    gateway.capture_net = '10.50'
    accepted = http.post('/capture', json={'order_id': order_ids[1]})
    assert accepted.status_code == 200, accepted.get_json()
    assert case.discount_ref.get().to_dict()['usedCount'] == 1
    assert gateway.capture_calls == 2
    assert db.document('orders/' + order_ids[0]).get().to_dict()['captured'] is False
    assert_revenue(http, case.event.id, 12, 10.5, 1.5, 1)


@pytest.mark.parametrize('started', [False, True])
def test_reservation_expiry_reclaims_only_unstarted_payment(
        http, discount_case, gateway, started):
    from datetime import timedelta

    case = discount_case
    case.discount_ref.update({'maxUses': 1})
    response = http.post('/orders', json=checkout_payload(case))
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    repo = event_payment_api.event_payment_service.discount_code_repository
    token = repo.reserve_usage(case.discount_ref.id, 'interrupted-order')
    assert repo.reserve_usage(case.discount_ref.id, 'interrupted-order') == token
    if started:
        repo.begin_capture(case.discount_ref.id, 'interrupted-order', token)
    reservations = case.discount_ref.get().to_dict()['reservations']
    reservations['interrupted-order']['expiresAt'] = case.now - timedelta(days=1)
    case.discount_ref.update({'reservations': reservations})
    gateway.capture_net = '10.50'
    capture = http.post('/capture', json={'order_id': order_id})
    assert capture.status_code == (409 if started else 200), capture.get_json()
    assert gateway.capture_calls == (0 if started else 1)
    assert case.discount_ref.get().to_dict()['usedCount'] == (0 if started else 1)
    if not started:
        with pytest.raises(ConflictError):
            repo.begin_capture(case.discount_ref.id, 'interrupted-order', token)
    else:
        assert_no_provisioning(http, case)


@pytest.mark.parametrize('started', [False, True])
def test_admin_capacity_update_respects_reserved_and_inflight_slots(
        http, discount_case, started):
    from errors.service_errors import ValidationError

    case = discount_case
    repo = event_payment_api.event_payment_service.discount_code_repository
    tokens = {order: repo.reserve_usage(case.discount_ref.id, order) for order in ('a', 'b')}
    if started:
        for order, token in tokens.items():
            repo.begin_capture(case.discount_ref.id, order, token)
    with pytest.raises(ValidationError):
        repo.update(case.discount_ref.id, {'max_uses': 1}, 'test-admin')
    assert case.discount_ref.get().to_dict()['maxUses'] == 2
    for order, token in tokens.items():
        if not started:
            repo.begin_capture(case.discount_ref.id, order, token)
        repo.consume_reservation(case.discount_ref.id, order, token)
    assert case.discount_ref.get().to_dict()['usedCount'] == 2
