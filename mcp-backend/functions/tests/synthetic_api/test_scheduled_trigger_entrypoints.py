"""Real Firestore checks for scheduled trigger entrypoints."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from config.firebase_config import db
from models import EntranceScan
from models.scan_token import ScanToken
from triggers import analytics_trigger, cleanup_trigger, new_year_trigger


def test_new_year_entrypoint_invalidates_active_memberships_only(sample):
    inactive_ref = db.document(f"memberships/{sample.people[1].id}")
    inactive_ref.update({"subscription_valid": False})
    refs = [db.document(f"memberships/{person.id}") for person in sample.people]
    original = [ref.get().to_dict() for ref in refs]
    expected = [dict(payload) for payload in original]
    expected[0]["subscription_valid"] = False

    event = SimpleNamespace()
    new_year_trigger.invalidate_memberships_new_year.__wrapped__(event)
    after_first_call = [ref.get().to_dict() for ref in refs]
    assert after_first_call == expected

    new_year_trigger.invalidate_memberships_new_year.__wrapped__(event)
    assert [ref.get().to_dict() for ref in refs] == after_first_call


def test_nightly_analytics_entrypoint_enqueues_full_rebuild_once(sample):
    event = SimpleNamespace()
    analytics_trigger.rebuild_analytics_nightly.__wrapped__(event)

    jobs = list(db.collection("analytics_jobs").stream())
    assert len(jobs) == 1
    assert jobs[0].to_dict()["type"] == "analytics_rebuild"
    assert jobs[0].to_dict()["scope"] == "all"
    assert jobs[0].to_dict()["status"] == "queued"
    assert jobs[0].to_dict()["reason"] == "scheduled_full_rebuild"
    job_id = jobs[0].id
    payload = jobs[0].to_dict()

    # The scheduled entrypoint enqueues only; no worker is invoked here.
    analytics_trigger.rebuild_analytics_nightly.__wrapped__(event)
    jobs_after_replay = list(db.collection("analytics_jobs").stream())
    assert len(jobs_after_replay) == 1
    assert jobs_after_replay[0].id == job_id
    # A queued replay refreshes the kick timestamps without creating another job.
    volatile = {"updated_at", "last_kicked_at"}
    assert {key: value for key, value in jobs_after_replay[0].to_dict().items() if key not in volatile} == {
        key: value for key, value in payload.items() if key not in volatile
    }


def test_cleanup_entrypoint_removes_old_tokens_and_preserves_recent_and_history(sample):
    now = datetime.now(timezone.utc)
    old_ref = db.document("scan_tokens/scheduled-old")
    kept_ref = db.document("scan_tokens/scheduled-future")
    old_ref.set(ScanToken(event_id=sample.event.id, expires_at=now - timedelta(days=8)).to_firestore())
    kept_ref.set(ScanToken(event_id=sample.event.id, expires_at=now + timedelta(days=1)).to_firestore())
    history_ref = db.document(
        f"entrance_scans/{sample.event.id}/scans/{sample.people[0].id}"
    )
    history_ref.set(EntranceScan(
        scan_token=old_ref.id,
        scanned_at=now - timedelta(days=10),
    ).to_firestore())
    kept_token_before = kept_ref.get().to_dict()
    history_before = history_ref.get().to_dict()

    event = SimpleNamespace()
    cleanup_trigger.cleanup_stale_data.__wrapped__(event)

    assert not old_ref.get().exists
    assert kept_ref.get().to_dict() == kept_token_before
    assert history_ref.get().to_dict() == history_before

    cleanup_trigger.cleanup_stale_data.__wrapped__(event)
    assert not old_ref.get().exists
    assert kept_ref.get().to_dict() == kept_token_before
    assert history_ref.get().to_dict() == history_before
