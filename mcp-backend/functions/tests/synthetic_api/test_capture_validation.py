"""PAY-10: reject unverifiable capture facts without forgetting the payment."""
import pytest
from google.cloud import firestore

from config.firebase_config import db
from models import DiscountCode, DiscountType
from tests.synthetic_api.test_concurrent_checkout import documents
from tests.synthetic_api.test_purchase_entrance_stats import assert_revenue, order_payload


@pytest.mark.parametrize('discount', [False, True])
@pytest.mark.parametrize('problem', [
    'invalid_amount', 'null_amount', 'missing_amount', 'nan_amount', 'infinite_amount',
    'negative_amount', 'null_total', 'missing_total', 'invalid_total', 'nan_total',
    'infinite_total', 'negative_total', 'matched_negative', 'matched_infinity',
    'not_final', 'missing_final', 'string_final', 'numeric_final',
    'amount_container_string', 'amount_container_list', 'extreme_amount', 'over_tolerance_precision',
])
def test_pay10_anomaly_blocks_tickets_and_keeps_capture_guard(
        http, sample, gateway, monkeypatch, discount, problem):
    if discount:
        sample.people = sample.people[:1]
        code = DiscountCode(id='pay10-discount', event_id=sample.event.id, code='CHECK',
                            discount_type=DiscountType.PERCENTAGE, discount_value=50,
                            max_uses=1, used_count=0, is_active=True)
        db.document('discount_codes/' + code.id).set(code.to_firestore())
        gateway.capture_net = '10.50'
    payload = order_payload(sample)
    if discount:
        payload['cart'][0]['discountCode'] = 'CHECK'
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    order_id = response.get_json()['id']
    total_changes = {'null_total': None, 'missing_total': firestore.DELETE_FIELD,
                     'invalid_total': 'invalid', 'nan_total': float('nan'),
                     'infinite_total': float('inf'), 'negative_total': -10,
                     'matched_negative': -10, 'matched_infinity': float('inf')}
    if problem in total_changes:
        db.document('orders/' + order_id).update({'total': total_changes[problem]})
    before_memberships = documents('memberships')
    original = gateway.capture_order

    def anomalous_capture(target):
        result = original(target)
        capture = result.payload['purchase_units'][0]['payments']['captures'][0]
        amounts = {'invalid_amount': 'invalid', 'null_amount': None, 'nan_amount': 'NaN',
                   'infinite_amount': 'Infinity', 'negative_amount': '-10.00',
                   'matched_negative': '-10.00', 'matched_infinity': 'Infinity'}
        if problem.startswith('amount_container_'):
            capture['amount'] = 'invalid' if problem.endswith('string') else ['10.00']
        elif problem == 'extreme_amount':
            capture['amount']['value'] = '1E+1000000'
        elif problem == 'over_tolerance_precision':
            total = '12' if discount else '44'
            capture['amount']['value'] = total + '.010000000000000000000000000001'
        elif problem in amounts:
            capture['amount']['value'] = amounts[problem]
        elif problem == 'missing_amount':
            capture.pop('amount')
        elif problem == 'missing_total':
            # Missing data must not be treated as a legitimate stored zero total.
            capture['amount']['value'] = '0.00'
        elif problem == 'missing_final':
            capture.pop('final_capture')
        elif problem in ('not_final', 'string_final', 'numeric_final'):
            capture['final_capture'] = {'not_final': False, 'string_final': 'false', 'numeric_final': 1}[problem]
        return result

    with monkeypatch.context() as patch:
        patch.setattr(gateway, 'capture_order', anomalous_capture)
        result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 400, result.get_json()
    order = db.document('orders/' + order_id).get().to_dict()
    assert order['captured'] is True and order['orderStatus'] == 'PAYMENT_CAPTURED'
    assert not order.get('purchase_id')
    assert not documents('purchases')
    assert not documents(f'participants/{sample.event.id}/participants_event')
    assert documents('memberships') == before_memberships
    assert_revenue(http, sample.event.id, 0, 0, 0, 0)
    if discount:
        data = db.document('discount_codes/pay10-discount').get().to_dict()
        assert data['usedCount'] == 0
        assert data['reservations'][order_id]['state'] == 'capturing'
        assert not documents('discount_codes/pay10-discount/reservation_receipts')
    retry = http.post('/capture', json={'order_id': order_id})
    assert retry.status_code == 409, retry.get_json()
    assert retry.get_json()['code'] == 'ORDER_PROVISIONING_INCOMPLETE'
    assert gateway.capture_calls == 1
