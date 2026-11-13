"""OPS-08: real Firestore cleanup boundaries, stale snapshots and scan retention."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from config.firebase_config import db
from models import EntranceScan
from models.scan_token import ScanToken
from triggers import cleanup_trigger

NOW = datetime(2026, 11, 12, 12, tzinfo=timezone.utc)


def token(sample, identifier, expires_at, *, active=True):
    ref = db.document('scan_tokens/' + identifier)
    ref.set(ScanToken(event_id=sample.event.id, expires_at=expires_at, is_active=active).to_firestore())
    return ref


def scan(sample, token_id):
    ref = db.document(f'entrance_scans/{sample.event.id}/scans/{sample.people[0].id}')
    ref.set(EntranceScan(scan_token=token_id, scanned_at=NOW - timedelta(days=10)).to_firestore())
    return ref


@pytest.mark.parametrize('active', [False, True])
def test_cleanup_deletes_only_strictly_older_tokens_and_preserves_history(sample, active):
    old = token(sample, 'old', NOW - timedelta(days=7, microseconds=1), active=active)
    exact = token(sample, 'exact', NOW - timedelta(days=7))
    recent = token(sample, 'recent', NOW - timedelta(days=7) + timedelta(microseconds=1))
    future = token(sample, 'future', NOW + timedelta(days=1))
    history = scan(sample, old.id)
    before_history = history.get().to_dict()
    kept = {ref.id: ref.get().to_dict() for ref in (exact, recent, future)}

    assert cleanup_trigger._cleanup_scan_tokens(NOW) == 1
    assert not old.get().exists
    for ref in (exact, recent, future):
        assert ref.get().to_dict() == kept[ref.id]
    assert history.get().to_dict() == before_history
    assert cleanup_trigger._cleanup_scan_tokens(NOW) == 0


def test_invalid_expiry_is_retained_without_blocking_cleanup(sample):
    malformed = token(sample, 'malformed', 'not-a-timestamp')
    old = token(sample, 'old-valid', NOW - timedelta(days=8))
    missing = token(sample, 'missing', None)
    kept = {ref.id: ref.get().to_dict() for ref in (malformed, missing)}

    assert cleanup_trigger._cleanup_scan_tokens(NOW) == 1
    assert not old.get().exists
    for ref in (malformed, missing):
        assert ref.get().to_dict() == kept[ref.id]


@pytest.mark.parametrize('change', ['renewed', 'removed'])
def test_changed_snapshot_is_not_deleted_or_counted_and_other_tokens_are_cleaned(sample, monkeypatch, change):
    racing = token(sample, 'racing', NOW - timedelta(days=8))
    other = token(sample, 'other-old', NOW - timedelta(days=9))
    history = scan(sample, racing.id)
    before_history = history.get().to_dict()
    collection = db.collection('scan_tokens')

    def stream_with_change():
        for snapshot in collection.stream():
            def read_stale_data(snapshot=snapshot):
                data = snapshot.to_dict()
                if snapshot.id == racing.id:
                    if change == 'renewed':
                        racing.update({'expires_at': NOW + timedelta(days=1)})
                    else:
                        racing.delete()
                return data
            yield SimpleNamespace(to_dict=read_stale_data, reference=snapshot.reference,
                                  update_time=snapshot.update_time)

    monkeypatch.setattr(cleanup_trigger, 'db', SimpleNamespace(
        collection=lambda name: SimpleNamespace(stream=stream_with_change) if name == 'scan_tokens'
        else db.collection(name), batch=db.batch, write_option=db.write_option))

    assert cleanup_trigger._cleanup_scan_tokens(NOW) == 1
    assert not other.get().exists
    if change == 'renewed':
        assert racing.get().to_dict()['expires_at'] == NOW + timedelta(days=1)
    else:
        assert not racing.get().exists
    assert history.get().to_dict() == before_history


def test_more_than_500_expired_tokens_are_removed_without_touching_scans(sample):
    data = ScanToken(event_id=sample.event.id, expires_at=NOW - timedelta(days=8)).to_firestore()
    for start in (0, 400):
        batch = db.batch()
        for index in range(start, min(start + 400, 501)):
            batch.set(db.document(f'scan_tokens/old-{index:03d}'), data)
        batch.commit()
    history = scan(sample, 'old-000')
    before_history = history.get().to_dict()

    assert cleanup_trigger._cleanup_scan_tokens(NOW) == 501
    assert list(db.collection('scan_tokens').stream()) == []
    assert history.get().to_dict() == before_history
