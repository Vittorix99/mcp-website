"""OPS-07: local scheduled cleanup against actual checkout records and CAS races."""
from datetime import timedelta

import pytest
from google.cloud import firestore
from google.cloud.firestore_v1.document import DocumentReference

from api.public import event_payment_api
from config.firebase_config import db
from triggers.cleanup_trigger import _cleanup_orders
from tests.synthetic_api.test_concurrent_checkout import documents
from tests.synthetic_api.test_order_recovery import create_checkout_order, pending_order
from tests.synthetic_api.test_purchase_entrance_stats import create_order


def age_order(order_id, now):
    db.document('orders/' + order_id).update({'createdAt': now - timedelta(hours=25)})


def test_fresh_checkout_created_by_repository_survives_cleanup(http, sample, gateway):
    order_id = create_order(http, sample)
    before = documents('orders')
    assert 'createdAt' in before[order_id]
    assert before[order_id]['captureStarted'] is False
    assert _cleanup_orders(sample.now) == 0
    assert documents('orders') == before
    assert gateway.capture_calls == 0


@pytest.mark.parametrize('seconds,deleted', [(-1, 0), (0, 0), (1, 1)])
def test_cleanup_24_hour_boundary(http, sample, gateway, seconds, deleted):
    order_id = create_order(http, sample)
    db.document('orders/' + order_id).update({'createdAt': sample.now - timedelta(hours=24, seconds=seconds)})
    assert _cleanup_orders(sample.now) == deleted
    assert db.document('orders/' + order_id).get().exists is (not deleted)
    assert gateway.capture_calls == 0


@pytest.mark.parametrize('case,deleted', [('legacy_marker', 0), ('missing_timestamp', 0),
    ('bad_timestamp', 0), ('conflicting_dates', 0), ('legacy_alias', 1),
    ('bad_status_list', 0), ('bad_status_map', 0), ('bad_purchase_list', 0), ('bad_purchase_map', 0)])
def test_legacy_and_uncertain_cleanup_evidence_is_not_guessed(http, sample, gateway, case, deleted):
    order_id = create_order(http, sample)
    ref = db.document('orders/' + order_id)
    age_order(order_id, sample.now)
    if case == 'legacy_marker':
        ref.update({'captureStarted': firestore.DELETE_FIELD})
    elif case == 'missing_timestamp':
        ref.update({'createdAt': firestore.DELETE_FIELD})
    elif case == 'bad_timestamp':
        ref.update({'createdAt': 'invalid'})
    elif case == 'conflicting_dates':
        ref.update({'created_at': sample.now})
    elif case == 'legacy_alias':
        ref.update({'createdAt': firestore.DELETE_FIELD, 'created_at': sample.now - timedelta(hours=25)})
    elif case.startswith('bad_status'):
        ref.update({'orderStatus': [] if case.endswith('list') else {}})
    else:
        ref.update({'purchase_id': [] if case.endswith('list') else {}})
    before = documents('orders')
    assert _cleanup_orders(sample.now) == deleted
    assert documents('orders') == ({} if deleted else before)
    assert gateway.capture_calls == 0


@pytest.mark.parametrize('discount', [False, True])
def test_provider_window_is_fenced_before_cleanup(http, sample, gateway, monkeypatch, discount):
    order_id = create_checkout_order(http, sample, gateway, discount)
    age_order(order_id, sample.now)
    original = gateway.capture_order
    def provider(target):
        assert db.document('orders/' + target).get().to_dict()['captureStarted'] is True
        assert _cleanup_orders(sample.now) == 0
        return original(target)
    monkeypatch.setattr(gateway, 'capture_order', provider)
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    assert gateway.capture_calls == 1
    assert db.document('orders/' + order_id).get().to_dict()['captured'] is True
    assert len(documents('purchases')) == 1


@pytest.mark.parametrize('discount', [False, True])
def test_cleanup_winner_cancels_capture_before_provider(http, sample, gateway, monkeypatch, discount):
    order_id = create_checkout_order(http, sample, gateway, discount)
    age_order(order_id, sample.now)
    repo = event_payment_api.event_payment_service.order_repository
    original = repo.mark_capture_started
    def start(target):
        assert _cleanup_orders(sample.now) == 1
        return original(target)
    monkeypatch.setattr(repo, 'mark_capture_started', start)
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 404, result.get_json()
    assert gateway.capture_calls == 0
    assert not db.document('orders/' + order_id).get().exists
    assert not documents('purchases')
    assert not documents(f'participants/{sample.event.id}/participants_event')
    if discount:
        data = db.document('discount_codes/recovery-discount').get().to_dict()
        assert data['usedCount'] == 0
        assert data['reservations'][order_id]['state'] == 'reserved'


def test_capture_start_after_cleanup_snapshot_wins_conditional_delete(http, sample, gateway, monkeypatch):
    order_id = create_order(http, sample)
    age_order(order_id, sample.now)
    repo = event_payment_api.event_payment_service.order_repository
    original = DocumentReference.delete
    def before_delete(ref, *args, **kwargs):
        if ref.path == 'orders/' + order_id:
            repo.mark_capture_started(order_id)
        return original(ref, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(DocumentReference, 'delete', before_delete)
        assert _cleanup_orders(sample.now) == 0
    assert db.document('orders/' + order_id).get().to_dict()['captureStarted'] is True
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    assert gateway.capture_calls == 1
    assert len(documents('purchases')) == 1


@pytest.mark.parametrize('discount', [False, True])
def test_unknown_paid_response_remains_recoverable_after_cleanup(http, sample, gateway, monkeypatch, discount):
    order_id = pending_order(http, sample, gateway, monkeypatch, 'provider_response', discount)
    age_order(order_id, sample.now)
    before = documents('orders')
    assert before[order_id]['captured'] is False and before[order_id]['captureStarted'] is True
    assert _cleanup_orders(sample.now) == 0
    assert documents('orders') == before
    result = http.post('/recover-order', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    assert gateway.capture_calls == 1
    assert len(documents('purchases')) == 1
    assert _cleanup_orders(sample.now) == 0


def test_completed_order_and_purchase_survive_cleanup(http, sample, gateway):
    order_id = create_order(http, sample)
    result = http.post('/capture', json={'order_id': order_id})
    assert result.status_code == 200, result.get_json()
    age_order(order_id, sample.now)
    before = {path: documents(path) for path in ('orders', 'purchases',
              f'participants/{sample.event.id}/participants_event')}
    assert _cleanup_orders(sample.now) == 0
    assert {path: documents(path) for path in before} == before
    assert gateway.capture_calls == 1
