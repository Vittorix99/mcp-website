"""OPS-08: scan token cleanup policy against an in-memory Firestore boundary."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from triggers import cleanup_trigger as module


NOW = datetime(2026, 11, 12, 12, tzinfo=timezone.utc)
THRESHOLD = NOW - timedelta(days=7)
OLD = THRESHOLD - timedelta(seconds=1)


class Ref:
    def __init__(self, client, key):
        self.client, self.key = client, key

    def delete(self, option=None):
        if option is not None and option != self.client.versions[self.key]:
            raise AssertionError("stale version supplied for token deletion")
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
        self.versions = {key: object() for key in rows}

    def collection(self, name):
        assert name == "scan_tokens"

        def stream():
            for key, data in list(self.rows.items()):
                snapshot = deepcopy(data)
                yield SimpleNamespace(
                    to_dict=lambda data=snapshot: data,
                    reference=Ref(self, key),
                    update_time=self.versions[key],
                )

        return SimpleNamespace(stream=stream)

    def write_option(self, *, last_update_time):
        return last_update_time

    def batch(self):
        return Batch()


def token(expires_at, **changes):
    return {"expires_at": expires_at, **changes}


def run_cleanup(monkeypatch, rows):
    client = Client(rows)
    monkeypatch.setattr(module, "db", client)
    deleted = module._cleanup_scan_tokens(NOW)
    return deleted, client.rows


@pytest.mark.parametrize(
    ("expires_at", "should_delete"),
    [
        (THRESHOLD - timedelta(microseconds=1), True),
        (THRESHOLD, False),
        (THRESHOLD + timedelta(microseconds=1), False),
        (NOW + timedelta(days=1), False),
    ],
    ids=["older-than-seven-days", "exactly-seven-days", "within-seven-days", "future"],
)
def test_cleanup_uses_strict_seven_day_expiry_boundary(monkeypatch, expires_at, should_delete):
    rows = {"candidate": token(expires_at)}
    deleted, remaining = run_cleanup(monkeypatch, rows)
    assert deleted == int(should_delete)
    assert remaining == ({} if should_delete else rows)


@pytest.mark.parametrize("active", [True, False])
def test_active_state_does_not_change_old_expiry_eligibility(monkeypatch, active):
    rows = {"candidate": token(OLD, is_active=active)}
    deleted, remaining = run_cleanup(monkeypatch, rows)
    assert deleted == 1
    assert remaining == {}


@pytest.mark.parametrize(
    "invalid_expiry",
    [None, "2026-11-01T12:00:00Z", "not-a-timestamp", 42, True, [], {}],
    ids=["none", "iso-string", "invalid-string", "number", "boolean", "list", "dict"],
)
def test_invalid_expiry_is_retained_and_does_not_abort_later_deletion(
    monkeypatch, invalid_expiry
):
    rows = {
        "invalid": token(invalid_expiry),
        "old": token(OLD),
    }
    deleted, remaining = run_cleanup(monkeypatch, rows)
    assert deleted == 1
    assert remaining == {"invalid": rows["invalid"]}


def test_naive_expiry_uses_utc_convention(monkeypatch):
    rows = {"naive-old": token(OLD.replace(tzinfo=None))}
    deleted, remaining = run_cleanup(monkeypatch, rows)
    assert deleted == 1
    assert remaining == {}


def test_missing_expiry_is_retained_without_blocking_other_tokens(monkeypatch):
    deleted, remaining = run_cleanup(monkeypatch, {"missing": {}, "old": token(OLD)})
    assert deleted == 1
    assert remaining == {"missing": {}}


def test_aware_offset_expiry_compares_by_instant(monkeypatch):
    same_instant = OLD.astimezone(timezone(timedelta(hours=5, minutes=30)))
    rows = {"offset-old": token(same_instant)}
    deleted, remaining = run_cleanup(monkeypatch, rows)
    assert deleted == 1
    assert remaining == {}


def test_mixed_cleanup_is_idempotent(monkeypatch):
    rows = {
        "old": token(OLD),
        "boundary": token(THRESHOLD),
        "future": token(NOW + timedelta(days=1)),
    }
    client = Client(rows)
    monkeypatch.setattr(module, "db", client)

    assert module._cleanup_scan_tokens(NOW) == 1
    assert client.rows == {"boundary": rows["boundary"], "future": rows["future"]}
    assert module._cleanup_scan_tokens(NOW) == 0
    assert client.rows == {"boundary": rows["boundary"], "future": rows["future"]}
