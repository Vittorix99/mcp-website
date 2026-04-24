import logging
from datetime import datetime, timedelta, timezone
from typing import List

from firebase_functions import scheduler_fn
from google.cloud import firestore

from config.firebase_config import db

logger = logging.getLogger("cleanup_trigger")

_BATCH_SIZE = 500


@scheduler_fn.on_schedule(schedule="0 3 * * *", timezone="Europe/Rome")
def cleanup_stale_data(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Runs daily at 03:00 Europe/Rome. Removes:
    - Abandoned PayPal orders (never captured, created_at > 24h ago)
    - Expired scan tokens (expires_at > 7 days ago)
    - Failed jobs (status=failed, created_at > 30 days ago)
    """
    now = datetime.now(timezone.utc)
    orders_deleted = _cleanup_orders(now)
    tokens_deleted = _cleanup_scan_tokens(now)
    jobs_deleted = _cleanup_failed_jobs(now)
    logger.info(
        "cleanup_stale_data: deleted orders=%d scan_tokens=%d failed_jobs=%d",
        orders_deleted, tokens_deleted, jobs_deleted,
    )


def _batch_delete(refs: List) -> int:
    batch = db.batch()
    count = 0
    total = 0
    for ref in refs:
        batch.delete(ref)
        count += 1
        total += 1
        if count == _BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            count = 0
    if count:
        batch.commit()
    return total


def _to_utc(ts) -> datetime:
    if ts is None:
        return None
    if hasattr(ts, "tzinfo") and ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def _cleanup_orders(now: datetime) -> int:
    """Delete orders that were never captured and are older than 24 hours."""
    threshold = now - timedelta(hours=24)
    refs = []
    for doc in db.collection("orders").stream():
        data = doc.to_dict() or {}
        if data.get("captured"):
            continue
        created_at = _to_utc(data.get("created_at"))
        if created_at is None or created_at < threshold:
            refs.append(doc.reference)
    deleted = _batch_delete(refs)
    logger.info("cleanup_orders: %d ordini abbandonati eliminati", deleted)
    return deleted


def _cleanup_scan_tokens(now: datetime) -> int:
    """Delete scan tokens whose expiry was more than 7 days ago."""
    threshold = now - timedelta(days=7)
    refs = []
    for doc in db.collection("scan_tokens").stream():
        data = doc.to_dict() or {}
        expires_at = _to_utc(data.get("expires_at"))
        if expires_at is not None and expires_at < threshold:
            refs.append(doc.reference)
    deleted = _batch_delete(refs)
    logger.info("cleanup_scan_tokens: %d token scaduti eliminati", deleted)
    return deleted


def _cleanup_failed_jobs(now: datetime) -> int:
    """Delete jobs with status=failed that are older than 30 days."""
    threshold = now - timedelta(days=30)
    refs = []
    for doc in db.collection("jobs").stream():
        data = doc.to_dict() or {}
        if data.get("status") != "failed":
            continue
        created_at = _to_utc(data.get("created_at"))
        if created_at is None or created_at < threshold:
            refs.append(doc.reference)
    deleted = _batch_delete(refs)
    logger.info("cleanup_failed_jobs: %d job falliti eliminati", deleted)
    return deleted
