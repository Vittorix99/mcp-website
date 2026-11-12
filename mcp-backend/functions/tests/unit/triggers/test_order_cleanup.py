"""OPS-07: real cleanup policy against an in-memory versioned delete boundary."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from google.api_core.exceptions import FailedPrecondition

from triggers import cleanup_trigger as module


NOW = datetime(2026, 11, 12, 12, tzinfo=timezone.utc)
OLD = NOW - timedelta(hours=25)


class Ref:
    def __init__(self, client, key):
        self.client, self.key = client, key

    def delete(self, option=None):
        if self.client.before_delete:
            self.client.before_delete(self.key)
        if option is not None and option != self.client.versions[self.key]:
            raise FailedPrecondition('Document changed')
        self.client.rows.pop(self.key, None)


class Batch:
    def __init__(self):
        self.refs = []

    def delete(self, ref):
        self.refs.append(ref)

    def commit(self):
        for ref in self.refs:
            ref.delete()


class Client:
    def __init__(self, rows):
        self.rows = deepcopy(rows)
        self.versions = {key: 1 for key in rows}
        self.before_delete = None

    def collection(self, name):
        assert name == 'orders'
        def stream():
            for key, data in list(self.rows.items()):
                snapshot = deepcopy(data)
                yield SimpleNamespace(to_dict=lambda data=snapshot: data,
                    reference=Ref(self, key), update_time=self.versions[key])
        return SimpleNamespace(stream=stream)

    def write_option(self, *, last_update_time):
        return last_update_time

    def batch(self):
        return Batch()


def abandoned(**changes):
    return {'createdAt': OLD, 'captured': False, 'captureStarted': False,
            'orderStatus': 'CREATED', **changes}


def run_cleanup(monkeypatch, row):
    client = Client({'order': row})
    monkeypatch.setattr(module, 'db', client)
    deleted = module._cleanup_orders(NOW)
    return deleted, client.rows


@pytest.mark.parametrize('created', [NOW, NOW - timedelta(hours=24), NOW + timedelta(days=1)])
def test_fresh_exact_boundary_and_future_orders_are_kept(monkeypatch, created):
    row = abandoned(createdAt=created)
    deleted, rows = run_cleanup(monkeypatch, row)
    assert deleted == 0 and rows == {'order': row}


def test_only_older_than_24_hours_is_deleted(monkeypatch):
    deleted, rows = run_cleanup(monkeypatch, abandoned())
    assert deleted == 1 and rows == {}


@pytest.mark.parametrize('changes', [
    {'captured': True}, {'captureStarted': True}, {'purchase_id': 'purchase'},
    {'orderStatus': 'PAYMENT_CAPTURED'}, {'orderStatus': 'PURCHASE_CREATED'},
    {'orderStatus': 'COMPLETED'}, {'orderStatus': 'UNKNOWN'}, {'captured': None},
    {'captureStarted': None}, {'captureStarted': 'false'},
    {'orderStatus': []}, {'orderStatus': {}}, {'purchase_id': []}, {'purchase_id': {}},
])
def test_payment_evidence_or_ambiguity_always_preserves_order(monkeypatch, changes):
    row = abandoned(**changes)
    deleted, rows = run_cleanup(monkeypatch, row)
    assert deleted == 0 and rows == {'order': row}


@pytest.mark.parametrize('missing', ['createdAt', 'captured', 'captureStarted', 'orderStatus'])
def test_missing_cleanup_evidence_is_retained_for_manual_verification(monkeypatch, missing):
    row = abandoned()
    row.pop(missing)
    deleted, rows = run_cleanup(monkeypatch, row)
    assert deleted == 0 and rows == {'order': row}


@pytest.mark.parametrize('created', [None, 'invalid', '2026-11-01T12:00:00Z', 42])
def test_invalid_timestamp_does_not_delete_or_abort_cleanup(monkeypatch, created):
    row = abandoned(createdAt=created)
    deleted, rows = run_cleanup(monkeypatch, row)
    assert deleted == 0 and rows == {'order': row}


def test_legacy_timestamp_alias_is_accepted_when_payment_protocol_is_known(monkeypatch):
    row = abandoned(created_at=OLD)
    row.pop('createdAt')
    deleted, rows = run_cleanup(monkeypatch, row)
    assert deleted == 1 and rows == {}


def test_conflicting_timestamp_aliases_are_preserved(monkeypatch):
    row = abandoned(created_at=NOW)
    deleted, rows = run_cleanup(monkeypatch, row)
    assert deleted == 0 and rows == {'order': row}


def test_capture_start_after_snapshot_prevents_delete_and_other_orders_still_clean(monkeypatch):
    client = Client({'race': abandoned(), 'abandoned': abandoned()})
    def begin_capture(key):
        if key == 'race':
            client.rows[key]['captureStarted'] = True
            client.versions[key] += 1
    client.before_delete = begin_capture
    monkeypatch.setattr(module, 'db', client)
    assert module._cleanup_orders(NOW) == 1
    assert set(client.rows) == {'race'}
    assert client.rows['race']['captureStarted'] is True
