"""EVT-03: unavailable events must reject checkout before provider calls."""
import pytest

from config.firebase_config import db
from tests.synthetic_api.test_purchase_entrance_stats import create_order, order_payload


UNAVAILABLE_STATES = ('sold_out', 'coming_soon', 'ended')


@pytest.mark.parametrize('state', UNAVAILABLE_STATES)
def test_unavailable_event_rejects_new_order_before_provider(http, sample, gateway, state):
    db.document('events/' + sample.event.id).update({'status': state})

    response = http.post('/orders', json=order_payload(sample))

    assert response.status_code == 400, response.get_json()
    assert gateway.create_calls == gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
    assert not list(db.collection('purchases').stream())
    assert not list(db.collection(f'participants/{sample.event.id}/participants_event').stream())


@pytest.mark.parametrize('state', UNAVAILABLE_STATES)
def test_status_change_blocks_capture_without_mutation_and_reopening_allows_it(
        http, sample, gateway, state):
    order_id = create_order(http, sample)
    order_ref = db.document('orders/' + order_id)
    before = order_ref.get().to_dict()
    event_ref = db.document('events/' + sample.event.id)
    event_ref.update({'status': state})

    response = http.post('/capture', json={'order_id': order_id})

    assert response.status_code == 400, response.get_json()
    assert gateway.capture_calls == 0
    assert order_ref.get().to_dict() == before
    assert not list(db.collection('purchases').stream())
    assert not list(db.collection(f'participants/{sample.event.id}/participants_event').stream())

    event_ref.update({'status': 'active'})
    resumed = http.post('/capture', json={'order_id': order_id})
    assert resumed.status_code == 200, resumed.get_json()
    assert gateway.create_calls == gateway.capture_calls == 1
    assert len(list(db.collection('purchases').stream())) == 1
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 2


@pytest.mark.parametrize('state', UNAVAILABLE_STATES)
def test_completed_order_retry_returns_receipt_after_event_becomes_unavailable(
        http, sample, gateway, state):
    order_id = create_order(http, sample)
    captured = http.post('/capture', json={'order_id': order_id})
    assert captured.status_code == 200, captured.get_json()
    order_ref = db.document('orders/' + order_id)
    before = order_ref.get().to_dict()
    db.document('events/' + sample.event.id).update({'status': state})

    retry = http.post('/capture', json={'order_id': order_id})

    assert retry.status_code == 200, retry.get_json()
    assert retry.get_json() == captured.get_json()
    assert gateway.create_calls == gateway.capture_calls == 1
    assert order_ref.get().to_dict() == before
    assert len(list(db.collection('purchases').stream())) == 1
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 2
