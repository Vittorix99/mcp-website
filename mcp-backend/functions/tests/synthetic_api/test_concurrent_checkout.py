"""Controlled overlaps, real Firestore transactions, fake idempotent PayPal.

PAY-12 asserts the safety requirement (and may expose an application bug).
DIS-06 characterizes the post-capture loser; passing does not make it safe.
"""
from concurrent.futures import ThreadPoolExecutor
import faulthandler
import os
import sys
from threading import Barrier, Lock, Timer
from types import SimpleNamespace

import pytest

from api.public import event_payment_api
from config.firebase_config import db
from models import DiscountCode, DiscountType
from tests.synthetic_api.test_purchase_entrance_stats import assert_revenue, create_order, order_payload


CAPTURE_DEADLINE_SECONDS = 45


@pytest.fixture
def capture_log(gateway, monkeypatch):
    # Serialize only fake bookkeeping, never the service or repository workflow.
    lock = Lock()
    original = gateway.capture_order
    calls = []

    def capture(order_id):
        with lock:
            response = original(order_id)
            capture_id = response.payload['purchase_units'][0]['payments']['captures'][0]['id']
            calls.append((order_id, capture_id))
            return response

    monkeypatch.setattr(gateway, 'capture_order', capture)
    return calls


def concurrent_captures(http, order_ids):
    def capture(order_id):
        # A Flask test client and its request context belong to one worker only.
        with http.application.test_client() as client:
            response = client.post('/capture', json={'order_id': order_id})
            return response.status_code, response.get_json()

    def deadline_exceeded():
        print('Concurrent capture deadline exceeded; aborting pytest before database cleanup',
              file=sys.stderr, flush=True)
        faulthandler.dump_traceback()
        # Kill this dedicated test process: active writers must never outlive teardown.
        # emulators:exec owns emulator shutdown; a timeout may leave no JUnit report.
        os._exit(124)

    deadline = Timer(CAPTURE_DEADLINE_SECONDS, deadline_exceeded)
    deadline.daemon = True
    deadline.start()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(capture, order_id) for order_id in order_ids]
            return [future.result() for future in futures]
    finally:
        deadline.cancel()


def documents(path):
    return {doc.id: doc.to_dict() for doc in db.collection(path).stream()}


def test_same_order_concurrent_capture_has_one_purchase_and_provisioning(
        http, sample, gateway, capture_log, monkeypatch):
    """PAY-12: stale reads must not duplicate local purchases for one capture."""
    order_id = create_order(http, sample)
    repository = event_payment_api.event_payment_service.order_repository
    original_get = repository.get_model
    both_read = Barrier(2, timeout=10)

    def read_before_capture(target_id):
        order = original_get(target_id)
        assert target_id == order_id and order is not None and not order.captured
        both_read.wait()
        return order

    with monkeypatch.context() as patch:
        patch.setattr(repository, 'get_model', read_before_capture)
        results = concurrent_captures(http, [order_id, order_id])

    orders = documents('orders')
    purchases = documents('purchases')
    participants = documents(f'participants/{sample.event.id}/participants_event')
    calls_before_retry = list(capture_log)
    retry = http.post('/capture', json={'order_id': order_id})
    evidence = {'responses': results, 'calls': calls_before_retry, 'orders': orders,
                'purchases': purchases, 'participants': participants,
                'revenue': http.get('/revenue', query_string={'event_id': sample.event.id}).get_json(),
                'retry': (retry.status_code, retry.get_json())}
    # Include all persisted evidence even when the uniqueness requirement fails.
    assert all(status in (200, 409) for status, _ in results), evidence
    assert any(status == 200 for status, _ in results), evidence
    assert len(set(capture_id for _, capture_id in capture_log)) == 1, evidence
    assert capture_log == calls_before_retry, evidence
    assert len(purchases) == 1, evidence
    purchase_id, purchase = next(iter(purchases.items()))
    assert purchase['order_id'] == order_id, evidence
    assert purchase['transaction_id'] == capture_log[0][1], evidence
    assert purchase['participants_count'] == 2, evidence
    assert orders[order_id]['captured'] is True, evidence
    assert orders[order_id]['orderStatus'] == 'COMPLETED', evidence
    assert orders[order_id]['purchase_id'] == purchase_id, evidence
    assert len(participants) == 2, evidence
    assert {item['membershipId'] for item in participants.values()} == {
        member.id for member in sample.people}, evidence
    assert {item['purchase_id'] for item in participants.values()} == {purchase_id}, evidence
    for status, body in results:
        if status == 200:
            assert body['purchase_id'] == purchase_id, evidence
    assert retry.status_code == 200 and retry.get_json()['purchase_id'] == purchase_id, evidence
    assert documents('orders') == orders, evidence
    assert documents('purchases') == purchases, evidence
    assert documents(f'participants/{sample.event.id}/participants_event') == participants, evidence
    assert len(documents('memberships')) == 2, evidence
    assert_revenue(http, sample.event.id, 44, 42.5, 1.5, 2)


def test_last_discount_usage_concurrent_claim_keeps_post_capture_loser_explicit(
        http, sample, gateway, capture_log, monkeypatch):
    """DIS-06: one usage winner, but the losing order has already been captured."""
    code = DiscountCode(id='last-discount', event_id=sample.event.id, code='LAST',
                        discount_type=DiscountType.PERCENTAGE, discount_value=50,
                        max_uses=2, used_count=1, is_active=True)
    discount_ref = db.document('discount_codes/' + code.id)
    discount_ref.set(code.to_firestore())
    order_ids = []
    for member in sample.people:
        payload = order_payload(SimpleNamespace(event=sample.event, people=[member]))
        payload['cart'][0]['discountCode'] = 'LAST'
        response = http.post('/orders', json=payload)
        assert response.status_code == 201, response.get_json()
        order_ids.append(response.get_json()['id'])
    assert len(set(order_ids)) == 2
    assert discount_ref.get().to_dict()['usedCount'] == 1
    assert not documents('purchases')
    gateway.capture_net = '10.50'
    repository = event_payment_api.event_payment_service.discount_code_repository
    original_claim = repository.claim_usage
    both_captured = Barrier(2, timeout=10)

    def claim_after_both_captures(discount_id):
        assert discount_id == code.id
        both_captured.wait()
        # Keep the transaction intact: never synchronize inside its retry callback.
        return original_claim(discount_id)

    with monkeypatch.context() as patch:
        patch.setattr(repository, 'claim_usage', claim_after_both_captures)
        results = concurrent_captures(http, order_ids)

    evidence = {'responses': results, 'calls': capture_log, 'orders': documents('orders'),
                'purchases': documents('purchases'), 'discount': discount_ref.get().to_dict()}
    assert sorted(status for status, _ in results) == [200, 409], evidence
    winner = next(index for index, (status, _) in enumerate(results) if status == 200)
    loser = 1 - winner
    winner_id, loser_id = order_ids[winner], order_ids[loser]
    purchase_id = results[winner][1]['purchase_id']
    orders = evidence['orders']
    assert orders[winner_id]['captured'] is True, evidence
    assert orders[winner_id]['orderStatus'] == 'COMPLETED', evidence
    assert orders[winner_id]['purchase_id'] == purchase_id, evidence
    assert orders[loser_id]['captured'] is True, evidence
    assert orders[loser_id]['orderStatus'] == 'PAYMENT_CAPTURED', evidence
    assert not orders[loser_id].get('purchase_id'), evidence
    assert evidence['discount']['usedCount'] == 2, evidence
    assert set(evidence['purchases']) == {purchase_id}, evidence
    purchase = evidence['purchases'][purchase_id]
    assert purchase['order_id'] == winner_id, evidence
    assert purchase['discountCodeId'] == code.id, evidence
    assert purchase['participants_count'] == 1, evidence
    assert len(capture_log) == 2, evidence
    assert {order_id for order_id, _ in capture_log} == set(order_ids), evidence
    assert len({capture_id for _, capture_id in capture_log}) == 2, evidence
    participants_path = f'participants/{sample.event.id}/participants_event'
    participants = documents(participants_path)
    assert len(participants) == 1, evidence
    participant = next(iter(participants.values()))
    assert participant['membershipId'] == sample.people[winner].id, evidence
    assert participant['purchase_id'] == purchase_id, evidence
    assert_revenue(http, sample.event.id, 12, 10.5, 1.5, 1)

    calls_before_retry = list(capture_log)
    for index, order_id in enumerate(order_ids):
        retry = http.post('/capture', json={'order_id': order_id})
        if index == winner:
            assert retry.status_code == 200, retry.get_json()
            assert retry.get_json()['purchase_id'] == purchase_id
        else:
            assert retry.status_code == 409, retry.get_json()
            assert retry.get_json()['code'] == 'ORDER_PROVISIONING_INCOMPLETE'
    assert capture_log == calls_before_retry
    assert discount_ref.get().to_dict() == evidence['discount']
    assert documents('orders') == orders
    assert documents('purchases') == evidence['purchases']
    assert documents(participants_path) == participants
    assert len(documents('memberships')) == 2
    assert_revenue(http, sample.event.id, 12, 10.5, 1.5, 1)
