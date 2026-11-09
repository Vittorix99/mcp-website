"""Discount matrix slice: actual handlers/repositories, fake PayPal, no triggers."""
import pytest

from api.public import event_payment_api
from config.firebase_config import db
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
])
def test_discount_formula_capture_and_retry_use_exact_totals(
        http, discount_case, gateway, kind, value, price, discount, final, gross, net):
    """DIS-01/03/07: normalization, separate event fee, one usage despite retry."""
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
    """DIS-07: provider rejection precedes the usage claim and all provisioning."""
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
    assert case.discount_ref.get().to_dict() == before
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
