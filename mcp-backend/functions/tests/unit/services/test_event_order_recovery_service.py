from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from dto.preorder import OrderCaptureDTO
from errors.service_errors import ConflictError, ExternalServiceError
from models import Event, EventOrder
from services.payments.paypal_gateway import PayPalGatewayResponse
from tests.unit.services.test_event_payment_service import _make_service, _order_payload, _participant


@pytest.fixture
def recovery():
    from services.payments.event_order_recovery_service import EventOrderRecoveryService
    payments = _make_service()
    order = EventOrder(order_id='order-1', event_id='evt-1', total=10, event_price=10, captured=True,
                       participants=[_participant().to_payload()])
    payments.order_repository.order_data = order
    payments.event_repository.model = Event(title='Event', date=(datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y'),
                                             start_time='20:00', end_time='23:00')
    payments.purchase_repository.find_by_order = lambda _: None
    payload = _order_payload()
    payload['purchase_units'][0]['reference_id'] = 'evt-1'
    for amount in payload['purchase_units'][0]['payments']['captures'][0]['seller_receivable_breakdown'].values():
        amount['currency_code'] = 'EUR'
    reads = []
    def get_order(order_id):
        reads.append(order_id)
        return PayPalGatewayResponse(200, deepcopy(payload))
    payments.paypal_gateway = SimpleNamespace(get_order=get_order)
    return SimpleNamespace(service=EventOrderRecoveryService(payments), payments=payments,
                           order=order, payload=payload, reads=reads)


def test_verified_capture_recovers_purchase_and_participants_without_capture(recovery):
    case = recovery
    result = case.service.recover_order('order-1')
    assert result.purchase_id == 'pur-1'
    assert case.reads == ['order-1']
    assert len(case.payments.purchase_repository.created) == 1
    assert len(case.payments.participant_repository.created) == 1
    assert case.payments.order_repository.status_updates[-1] == ('order-1', 'COMPLETED')


@pytest.mark.parametrize('problem', ['membership', 'no_people', 'expired'])
def test_unsupported_local_state_rejected_before_provider_or_writes(recovery, problem):
    case = recovery
    if problem == 'membership':
        case.order.membership_targets = [_participant().to_payload()]
    elif problem == 'no_people':
        case.order.participants = []
    else:
        case.payments.event_repository.model.date = '01-01-2020'
    with pytest.raises(ConflictError):
        case.service.recover_order('order-1')
    assert case.reads == []
    assert case.payments.purchase_repository.created == []
    assert case.payments.order_repository.captured_updates == []


@pytest.mark.parametrize('field,value', [
    ('id', 'other-order'), ('reference_id', 'other-event'), ('currency_code', 'USD'),
    ('amount', '10.01'), ('amount', 'NaN'), ('amount', 'Infinity'),
    ('status', 'PENDING'), ('capture_status', 'REFUNDED'), ('capture_id', ''),
    ('final_capture', False), ('paypal_fee', ''), ('net_amount', '9.00'),
    ('create_time', 'nonsense'), ('multiple_captures', True),
])
def test_provider_inconsistency_never_mutates_local_records(recovery, field, value):
    case = recovery
    unit = case.payload['purchase_units'][0]
    capture = unit['payments']['captures'][0]
    if field in ('id', 'status'):
        case.payload[field] = value
    elif field == 'reference_id':
        unit[field] = value
    elif field == 'currency_code':
        capture['amount'][field] = value
    elif field == 'amount':
        capture['amount']['value'] = value
    elif field in ('paypal_fee', 'net_amount'):
        capture['seller_receivable_breakdown'][field]['value'] = value
    elif field == 'capture_status':
        capture['status'] = value
    elif field == 'capture_id':
        capture['id'] = value
    elif field == 'multiple_captures':
        unit['payments']['captures'].append(deepcopy(capture))
    else:
        capture[field] = value
    with pytest.raises(ConflictError):
        case.service.recover_order('order-1')
    assert case.payments.purchase_repository.created == []
    assert case.payments.participant_repository.created == []
    assert case.payments.order_repository.captured_updates == []


def test_provider_failure_is_explicit_without_any_local_writes(recovery):
    case = recovery
    case.payments.paypal_gateway = SimpleNamespace(get_order=lambda _: PayPalGatewayResponse(503, {}))
    with pytest.raises(ExternalServiceError):
        case.service.recover_order('order-1')
    assert case.payments.purchase_repository.created == []


def test_fee_currency_cannot_be_assumed_when_provider_omits_it(recovery):
    case = recovery
    breakdown = case.payload['purchase_units'][0]['payments']['captures'][0]['seller_receivable_breakdown']
    breakdown['paypal_fee'].pop('currency_code', None)
    with pytest.raises(ConflictError):
        case.service.recover_order('order-1')
    assert case.payments.purchase_repository.created == []


def test_unrelated_membership_lookup_cannot_enter_purchase(recovery):
    from models import Membership
    case = recovery
    member = Membership(id='other-member', email='other@example.test')
    case.order.membership_lookup = {'other@example.test': {**member.to_firestore(), 'id': member.id}}
    case.payments.membership_repository.get = lambda _: member
    with pytest.raises(ConflictError):
        case.service.recover_order('order-1')
    assert case.payments.purchase_repository.created == []


@pytest.mark.parametrize('corruption', ['participant_entry', 'participant_container', 'lookup_entry', 'lookup_container'])
def test_malformed_stored_checkout_is_not_partially_completed(recovery, corruption):
    case = recovery
    if corruption == 'participant_entry':
        case.order.participants.append(None)
    elif corruption == 'participant_container':
        case.order.participants = {'person': case.order.participants[0]}
    elif corruption == 'lookup_entry':
        case.order.membership_lookup = {'mario@example.com': None}
    else:
        case.order.membership_lookup = ['not a map']
    with pytest.raises(ConflictError):
        case.service.recover_order('order-1')
    assert case.payments.purchase_repository.created == []
    assert case.payments.participant_repository.created == []


@pytest.mark.parametrize('field,value', [
    ('event_price', float('nan')), ('event_price', float('inf')), ('event_price', -1),
    ('original_price', float('nan')), ('original_price', -1),
    ('discount_amount', float('nan')), ('discount_amount', float('inf')),
    ('event_fee', float('inf')),
])
def test_nonfinite_or_negative_stored_ticket_money_never_provisions(recovery, field, value):
    case = recovery
    setattr(case.order, field, value)
    with pytest.raises(ConflictError):
        case.service.recover_order('order-1')
    assert case.payments.purchase_repository.created == []
    assert case.payments.participant_repository.created == []
