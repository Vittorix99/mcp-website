"""Reservation lifecycle against an in-memory atomic Firestore batch boundary."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import repositories.discount_code_repository as module
from repositories.discount_code_repository import DiscountCodeRepository
from errors.service_errors import ConflictError, ValidationError
from google.api_core.exceptions import FailedPrecondition, Aborted


class Document:
    def __init__(self, store, path):
        self.store, self.path = store, path

    def update(self, data, option=None):
        self.store[self.path].update(deepcopy(data))

    def collection(self, name):
        return Collection(self.store, self.path + '/' + name)

    def get(self, transaction=None):
        data = deepcopy(self.store.get(self.path))
        return SimpleNamespace(exists=data is not None, to_dict=lambda: data, update_time="version-1", id=self.path.rsplit('/', 1)[-1])


class Collection:
    def __init__(self, store, path):
        self.store, self.path = store, path

    def document(self, key):
        return Document(self.store, self.path + '/' + key)


class Batch:
    def __init__(self):
        self.writes = []

    def update(self, ref, data, option=None):
        assert option == 'version-1'
        self.writes.append(lambda: ref.store[ref.path].update(deepcopy(data)))

    def set(self, ref, data):
        self.writes.append(lambda: ref.store.__setitem__(ref.path, deepcopy(data)))

    def commit(self):
        for write in self.writes:
            write()


@pytest.fixture
def reservations(monkeypatch):
    store = {'discount_codes/d': {'usedCount': 0, 'maxUses': 1, 'isActive': True}}
    repo = DiscountCodeRepository()
    repo.collection = Collection(store, 'discount_codes')
    monkeypatch.setattr(module, 'db', SimpleNamespace(
        batch=Batch, write_option=lambda *, last_update_time: last_update_time))
    return repo, store


def test_last_slot_is_reserved_before_it_is_consumed_and_retry_is_idempotent(reservations):
    repo, store = reservations
    token = repo.reserve_usage('d', 'a')
    assert repo.reserve_usage('d', 'a') == token
    assert store['discount_codes/d']['usedCount'] == 0
    with pytest.raises(ConflictError):
        repo.reserve_usage('d', 'b')
    repo.begin_capture('d', 'a', token)
    with pytest.raises(ConflictError):
        repo.begin_capture('d', 'a', token)
    repo.consume_reservation('d', 'a', token)
    repo.consume_reservation('d', 'a', token)
    assert store['discount_codes/d']['usedCount'] == 1
    assert store['discount_codes/d']['reservations'] == {}
    with pytest.raises(ConflictError):
        repo.reserve_usage('d', 'a')


def test_failed_payment_releases_slot_and_stale_release_cannot_release_retry(reservations):
    repo, store = reservations
    token = repo.reserve_usage('d', 'a')
    repo.begin_capture('d', 'a', token)
    repo.release_reservation('d', 'a', token)
    repo.release_reservation('d', 'a', token)
    new_token = repo.reserve_usage('d', 'a')
    assert new_token != token
    with pytest.raises(ConflictError):
        repo.release_reservation('d', 'a', token)
    with pytest.raises(ConflictError):
        repo.reserve_usage('d', 'b')
    assert store['discount_codes/d']['usedCount'] == 0


def test_expired_unstarted_slot_is_reclaimed_but_old_worker_cannot_capture(reservations):
    repo, store = reservations
    token = repo.reserve_usage('d', 'a')
    store['discount_codes/d']['reservations']['a']['expiresAt'] = datetime.now(timezone.utc) - timedelta(seconds=1)
    repo.reserve_usage('d', 'b')
    with pytest.raises(ConflictError):
        repo.begin_capture('d', 'a', token)
    assert store['discount_codes/d']['usedCount'] == 0


def test_inflight_or_unknown_capture_never_expires(reservations):
    repo, store = reservations
    token = repo.reserve_usage('d', 'a')
    repo.begin_capture('d', 'a', token)
    store['discount_codes/d']['reservations']['a']['expiresAt'] = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ConflictError):
        repo.reserve_usage('d', 'b')
    repo.consume_reservation('d', 'a', token)
    assert store['discount_codes/d']['usedCount'] == 1


def test_disabled_discount_does_not_reserve(reservations):
    repo, store = reservations
    store['discount_codes/d']['isActive'] = False
    with pytest.raises(ConflictError):
        repo.reserve_usage('d', 'a')
    assert 'reservations' not in store['discount_codes/d']


@pytest.mark.parametrize('started', [False, True])
def test_admin_cannot_reduce_capacity_below_live_reservations(reservations, started):
    repo, store = reservations
    store['discount_codes/d']['maxUses'] = 2
    for order in ('a', 'b'):
        token = repo.reserve_usage('d', order)
        if started:
            repo.begin_capture('d', order, token)
    with pytest.raises(ValidationError):
        repo.update('d', {'max_uses': 1}, 'admin')
    assert store['discount_codes/d']['maxUses'] == 2


def test_admin_reduction_counts_consumed_usage_but_not_expired_unstarted_slot(reservations):
    repo, store = reservations
    store['discount_codes/d'].update(maxUses=3, usedCount=1)
    repo.reserve_usage('d', 'a')
    with pytest.raises(ValidationError):
        repo.update('d', {'max_uses': 1}, 'admin')
    store['discount_codes/d']['reservations']['a']['expiresAt'] = datetime.now(timezone.utc) - timedelta(seconds=1)
    updated = repo.update('d', {'max_uses': 1}, 'admin')
    assert updated.max_uses == 1 and updated.used_count == 1


@pytest.mark.parametrize('error', [FailedPrecondition, Aborted])
def test_concurrent_reservation_rechecks_capacity_before_retrying(reservations, monkeypatch, error):
    repo, store = reservations
    attempts = []

    def lose_race(batch):
        attempts.append(1)
        store['discount_codes/d']['usedCount'] = 1
        raise error('Another checkout consumed the last slot')

    monkeypatch.setattr(Batch, 'commit', lose_race)
    with pytest.raises(ConflictError, match='esaurito'):
        repo.reserve_usage('d', 'a')
    assert len(attempts) == 1
    assert 'reservations' not in store['discount_codes/d']


def test_persistent_contention_is_bounded_without_issuing_writes(reservations, monkeypatch):
    repo, store = reservations
    attempts = []

    def lose_race(batch):
        attempts.append(1)
        raise FailedPrecondition('Changed')

    monkeypatch.setattr(Batch, 'commit', lose_race)
    with pytest.raises(ConflictError, match='contemporaneamente'):
        repo.reserve_usage('d', 'a')
    assert len(attempts) == 5
    assert 'reservations' not in store['discount_codes/d']


def test_admin_capacity_retry_rechecks_a_new_reservation(reservations, monkeypatch):
    repo, store = reservations
    store['discount_codes/d'].update(maxUses=3, usedCount=1)

    def concurrent_reservation(ref, data, option=None):
        assert option == 'version-1'
        store[ref.path]['reservations'] = {'b': {'state': 'capturing', 'token': 'b'}}
        raise FailedPrecondition('Checkout reserved a slot')

    monkeypatch.setattr(Document, 'update', concurrent_reservation)
    with pytest.raises(ValidationError):
        repo.update('d', {'max_uses': 1}, 'admin')
    assert store['discount_codes/d']['maxUses'] == 3


def test_recovery_consumes_attributable_slot_once_even_if_normal_worker_finishes_later(reservations):
    repo, store = reservations
    token = repo.reserve_usage('d', 'a')
    repo.begin_capture('d', 'a', token)
    repo.reconcile_usage('d', 'a')
    repo.reconcile_usage('d', 'a')
    repo.consume_reservation('d', 'a', token)
    assert store['discount_codes/d']['usedCount'] == 1
    assert store['discount_codes/d']['reservations'] == {}


@pytest.mark.parametrize('state', ['missing', 'reserved', 'released'])
def test_recovery_refuses_discount_without_attributable_capture_slot(reservations, state):
    repo, store = reservations
    if state != 'missing':
        token = repo.reserve_usage('d', 'a')
        if state == 'released':
            repo.begin_capture('d', 'a', token)
            repo.release_reservation('d', 'a', token)
    before = deepcopy(store)
    with pytest.raises(ConflictError):
        repo.reconcile_usage('d', 'a')
    assert store == before
