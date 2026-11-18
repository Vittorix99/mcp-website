"""EVT-04: real emulator capacity, fake payment provider, no cloud mutations."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier, local

import pytest

from api.public import event_payment_api
from config.firebase_config import db
from tests.synthetic_api.test_purchase_entrance_stats import create_order, order_payload


def reservation(order_id):
    order = db.document('orders/' + order_id).get().to_dict()
    return db.document(f"event_capacity/{order['eventId']}/reservations/{order['capacityReservationId']}")


@pytest.mark.parametrize('capacity', [None, 0, -1, 1])
def test_unconfigured_or_insufficient_capacity_rejects_whole_group(http, sample, gateway, capacity):
    db.document('events/' + sample.event.id).update({'maxParticipants': capacity})
    response = http.post('/orders', json=order_payload(sample))
    assert response.status_code == 409, response.get_json()
    assert gateway.create_calls == 0
    assert not list(db.collection('orders').stream())


def test_exact_capacity_reserved_at_create_and_rejected_before_second_provider_call(http, sample, gateway):
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    first = create_order(http, sample)
    held = reservation(first).get().to_dict()
    assert held['count'] == 2 and held['state'] == 'reserved'
    assert (held['expiresAt'] - held['createdAt']).total_seconds() == 600
    second = http.post('/orders', json=order_payload(sample))
    assert second.status_code == 409, second.get_json()
    assert gateway.create_calls == 1


@pytest.mark.parametrize('offset,expired', [(-1, False), (0, True), (1, True)])
def test_capture_deadline_before_at_after_ten_minutes(http, sample, gateway, monkeypatch, offset, expired):
    order_id = create_order(http, sample)
    ref = reservation(order_id)
    expiry = ref.get().to_dict()['expiresAt']
    from repositories import event_capacity_repository as capacity
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return (expiry + timedelta(seconds=offset)).astimezone(tz)
    monkeypatch.setattr(capacity, 'datetime', Clock)
    response = http.post('/capture', json={'order_id': order_id})
    assert response.status_code == (409 if expired else 200), response.get_json()
    assert gateway.capture_calls == (0 if expired else 1)
    if expired:
        assert db.document('orders/' + order_id).get().to_dict()['captureStarted'] is False


def test_expired_hold_releases_places_without_cleanup_job(http, sample, gateway):
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    first = create_order(http, sample)
    reservation(first).update({'expiresAt': datetime.now(timezone.utc) - timedelta(seconds=1)})
    second = create_order(http, sample)
    assert second != first
    assert http.post('/capture', json={'order_id': first}).status_code == 409
    assert gateway.capture_calls == 0


def test_provider_create_failure_releases_hold(http, sample, gateway):
    from services.payments.paypal_gateway import PayPalGatewayResponse
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    gateway.create_result = PayPalGatewayResponse(503, {})
    assert http.post('/orders', json=order_payload(sample)).status_code == 502
    gateway.create_result = None
    create_order(http, sample)
    assert gateway.create_calls == 2


@pytest.mark.parametrize('definitive', [True, False])
def test_failed_or_unknown_capture_releases_only_when_definitive(http, sample, gateway, definitive):
    from services.payments.paypal_gateway import PayPalGatewayResponse
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    order_id = create_order(http, sample)
    if definitive:
        gateway.bad_field, gateway.bad_state = 'capture_status', 'DECLINED'
    else:
        gateway.capture_result = PayPalGatewayResponse(503, {})
    failed = http.post('/capture', json={'order_id': order_id})
    assert failed.status_code == (400 if definitive else 502), failed.get_json()
    ref = reservation(order_id)
    if not definitive:
        ref.update({'expiresAt': datetime.now(timezone.utc) - timedelta(days=1)})
    gateway.capture_result = None
    retry = http.post('/orders', json=order_payload(sample))
    assert retry.status_code == (201 if definitive else 409), retry.get_json()
    assert gateway.capture_calls == 1


def test_legacy_order_without_hold_never_captures(http, sample, gateway):
    from google.cloud.firestore_v1 import DELETE_FIELD
    order_id = create_order(http, sample)
    db.document('orders/' + order_id).update({'capacityReservationId': DELETE_FIELD})
    response = http.post('/capture', json={'order_id': order_id})
    assert response.status_code == 409, response.get_json()
    assert gateway.capture_calls == 0


@pytest.mark.parametrize('iteration', range(3))
def test_two_simultaneous_orders_cannot_reserve_last_group(http, sample, gateway, monkeypatch, iteration):
    from tests.synthetic_api.test_concurrent_checkout import CAPTURE_DEADLINE_SECONDS
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    repo = event_payment_api.event_payment_service.capacity_repository
    original = repo._commit
    ready = Barrier(2, timeout=10)
    once = local()
    def commit(*args, **kwargs):
        if kwargs.get('create') and not getattr(once, 'waited', False):
            once.waited = True
            ready.wait()
        return original(*args, **kwargs)
    monkeypatch.setattr(repo, '_commit', commit)
    def order():
        with http.application.test_client() as client:
            response = client.post('/orders', json=order_payload(sample))
            return response.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(order) for _ in range(2)]
        statuses = [f.result(timeout=CAPTURE_DEADLINE_SECONDS) for f in futures]
    assert sorted(statuses) == [201, 409]
    assert gateway.create_calls == 1
    assert len(list(db.collection('orders').stream())) == 1


@pytest.mark.parametrize('capacity', [None, 0, 1])
def test_admin_can_overbook_and_delete_releases_online_capacity(http, sample, gateway, capacity):
    from dto.participant_api import ParticipantCreateRequestDTO
    from services.events.participants_service import ParticipantsService
    service = ParticipantsService()
    event_ref = db.document('events/' + sample.event.id)
    event_ref.update({'maxParticipants': capacity})
    ids = []
    for index in range(3):
        dto = ParticipantCreateRequestDTO.model_validate({
            'event_id': sample.event.id, 'name': 'Admin', 'surname': 'Guest',
            'email': f'manual-{index}@example.com', 'phone': f'+999999{index}',
            'birthdate': '01-01-1990', 'payment_method': 'omaggio', 'price': 0,
        })
        ids.append(service.create(dto).id)
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 3
    event_ref.update({'maxParticipants': 3})
    assert http.post('/orders', json=order_payload(sample)).status_code == 409
    for identifier in ids[:2]:
        service.delete(sample.event.id, identifier)
    create_order(http, sample)
    assert gateway.create_calls == 1


def test_paid_seats_are_not_double_counted_with_their_reservation(http, sample, gateway):
    db.document('events/' + sample.event.id).update({'maxParticipants': 4, 'allowDuplicates': True})
    first = create_order(http, sample)
    assert http.post('/capture', json={'order_id': first}).status_code == 200
    assert reservation(first).get().to_dict()['state'] == 'consumed'
    second = create_order(http, sample)
    assert http.post('/orders', json=order_payload(sample)).status_code == 409
    assert http.post('/capture', json={'order_id': second}).status_code == 200
    assert http.post('/orders', json=order_payload(sample)).status_code == 409
    assert gateway.capture_calls == 2


def test_partial_provisioning_keeps_only_unmaterialized_places_reserved(http, sample, gateway, monkeypatch):
    from tests.synthetic_api.test_order_recovery import pending_order
    db.document('events/' + sample.event.id).update({'maxParticipants': 4, 'allowDuplicates': True})
    first = pending_order(http, sample, gateway, monkeypatch, 'participant_created')
    second = create_order(http, sample)
    assert http.post('/orders', json=order_payload(sample)).status_code == 409
    recovered = http.post('/recover-order', json={'order_id': first})
    assert recovered.status_code == 200, recovered.get_json()
    assert reservation(first).get().to_dict()['state'] == 'consumed'
    assert http.post('/capture', json={'order_id': second}).status_code == 200
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 4
    assert gateway.capture_calls == 2


def test_admin_insert_does_not_revoke_an_existing_reservation(http, sample, gateway):
    from models import EventParticipant
    from repositories.participant_repository import ParticipantRepository
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    order_id = create_order(http, sample)
    ParticipantRepository().create_from_model(sample.event.id, EventParticipant(name='Manual guest'))
    response = http.post('/capture', json={'order_id': order_id})
    assert response.status_code == 200, response.get_json()
    assert len(list(db.collection(f'participants/{sample.event.id}/participants_event').stream())) == 3


@pytest.mark.parametrize('after_write', [False, True])
def test_order_save_failure_never_leaks_a_live_hold(http, sample, gateway, monkeypatch, after_write):
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    repo = event_payment_api.event_payment_service.order_repository
    original = repo.save
    def fail(*args):
        if after_write:
            original(*args)
        raise RuntimeError('Interrupted order save')
    with monkeypatch.context() as patch:
        patch.setattr(repo, 'save', fail)
        assert http.post('/orders', json=order_payload(sample)).status_code == 500
    create_order(http, sample)
    assert gateway.create_calls == 2


@pytest.mark.parametrize('field,value', [
    ('state', 'unknown'), ('state', None), ('count', True), ('count', -1),
    ('expiresAt', 'not-a-timestamp'),
])
def test_ambiguous_reservation_never_frees_capacity(http, sample, gateway, field, value):
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    first = create_order(http, sample)
    reservation(first).update({field: value})
    response = http.post('/orders', json=order_payload(sample))
    assert response.status_code == 409, response.get_json()
    assert gateway.create_calls == 1



def test_reused_provider_order_id_cannot_overwrite_a_paid_order(http, sample, gateway):
    from services.payments.paypal_gateway import PayPalGatewayResponse
    db.document('events/' + sample.event.id).update({'maxParticipants': 4, 'allowDuplicates': True})
    first = create_order(http, sample)
    assert http.post('/capture', json={'order_id': first}).status_code == 200
    ref = db.document('orders/' + first)
    before = ref.get().to_dict()
    gateway.create_result = PayPalGatewayResponse(201, {'id': first, 'status': 'CREATED'})
    response = http.post('/orders', json=order_payload(sample))
    assert response.status_code == 409, response.get_json()
    assert ref.get().to_dict() == before
    assert gateway.capture_calls == 1


def test_capture_claim_loses_to_expiry_reallocation_before_provider(http, sample, gateway, monkeypatch):
    from threading import Event
    from repositories import event_capacity_repository as capacity
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    first = create_order(http, sample)
    expiry = reservation(first).get().to_dict()['expiresAt']
    now = [expiry - timedelta(seconds=1)]
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now[0].astimezone(tz)
    monkeypatch.setattr(capacity, 'datetime', Clock)
    repo = event_payment_api.event_payment_service.capacity_repository
    original = repo._commit
    poised, resume = Event(), Event()
    def commit(*args, **kwargs):
        if args[2]['state'] == 'capturing':
            poised.set()
            assert resume.wait(timeout=10)
        return original(*args, **kwargs)
    monkeypatch.setattr(repo, '_commit', commit)
    def capture():
        with http.application.test_client() as client:
            return client.post('/capture', json={'order_id': first}).status_code
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(capture)
        try:
            assert poised.wait(timeout=10)
            now[0] = expiry
            second = create_order(http, sample)
        finally:
            resume.set()
        assert future.result(timeout=20) == 409
    assert second != first
    assert gateway.capture_calls == 0
    assert db.document('orders/' + first).get().to_dict()['captureStarted'] is False


def test_admin_insert_invalidates_stale_online_availability_read(http, sample, gateway, monkeypatch):
    from threading import Event
    from models import EventParticipant
    from repositories.participant_repository import ParticipantRepository
    db.document('events/' + sample.event.id).update({'maxParticipants': 2})
    repo = event_payment_api.event_payment_service.capacity_repository
    original = repo._commit
    poised, resume = Event(), Event()
    def commit(*args, **kwargs):
        if kwargs.get('create'):
            poised.set()
            assert resume.wait(timeout=10)
        return original(*args, **kwargs)
    monkeypatch.setattr(repo, '_commit', commit)
    def create():
        with http.application.test_client() as client:
            return client.post('/orders', json=order_payload(sample)).status_code
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(create)
        try:
            assert poised.wait(timeout=10)
            ParticipantRepository().create_from_model(sample.event.id, EventParticipant(name='Manual guest'))
        finally:
            resume.set()
        assert future.result(timeout=20) == 409
    assert gateway.create_calls == 0



def test_consumed_hold_cannot_recreate_participants_after_places_are_resold(http, sample, gateway, monkeypatch):
    from repositories.participant_repository import ParticipantRepository
    db.document('events/' + sample.event.id).update({'maxParticipants': 2, 'allowDuplicates': True})
    first = create_order(http, sample)
    orders = event_payment_api.event_payment_service.order_repository
    original = orders.update_status
    def fail_completion(order_id, status):
        if status == 'COMPLETED':
            raise RuntimeError('Interrupted after capacity completion')
        return original(order_id, status)
    with monkeypatch.context() as patch:
        patch.setattr(orders, 'update_status', fail_completion)
        assert http.post('/capture', json={'order_id': first}).status_code == 500
    assert reservation(first).get().to_dict()['state'] == 'consumed'
    people = db.collection(f'participants/{sample.event.id}/participants_event')
    for doc in people.stream():
        ParticipantRepository().delete(sample.event.id, doc.id)
    second = create_order(http, sample)
    response = http.post('/recover-order', json={'order_id': first})
    assert response.status_code == 409, response.get_json()
    assert list(people.stream()) == []
    assert reservation(second).get().to_dict()['state'] == 'reserved'
    assert gateway.capture_calls == 1


def test_expired_discounted_order_never_reserves_coupon_usage(http, sample, gateway):
    from tests.synthetic_api.test_order_recovery import create_checkout_order
    db.document('events/' + sample.event.id).update({'maxParticipants': 1})
    first = create_checkout_order(http, sample, gateway, discount=True)
    reservation(first).update({'expiresAt': datetime.now(timezone.utc) - timedelta(seconds=1)})
    response = http.post('/capture', json={'order_id': first})
    assert response.status_code == 409, response.get_json()
    code = db.document('discount_codes/recovery-discount').get().to_dict()
    assert code.get('reservations', {}) == {} and code['usedCount'] == 0
    payload = order_payload(sample)
    payload['cart'][0]['discountCode'] = 'RECOVER'
    second = http.post('/orders', json=payload)
    assert second.status_code == 201, second.get_json()
    captured = http.post('/capture', json={'order_id': second.get_json()['id']})
    assert captured.status_code == 200, captured.get_json()
    assert gateway.capture_calls == 1



def test_exhausted_coupon_releases_claimed_seats_without_provider_call(http, sample, gateway):
    from tests.synthetic_api.test_order_recovery import create_checkout_order
    db.document('events/' + sample.event.id).update({'maxParticipants': 1})
    first = create_checkout_order(http, sample, gateway, discount=True)
    db.document('discount_codes/recovery-discount').update({'usedCount': 1})
    response = http.post('/capture', json={'order_id': first})
    assert response.status_code == 409, response.get_json()
    assert reservation(first).get().to_dict()['state'] == 'released'
    create_order(http, sample)
    assert gateway.capture_calls == 0
