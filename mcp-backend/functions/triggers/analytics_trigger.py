import logging

from firebase_functions import firestore_fn, scheduler_fn

from config.firebase_config import region
from services.core.analytics_snapshot_service import AnalyticsSnapshotService

logger = logging.getLogger("analytics_trigger")
analytics_snapshot_service = AnalyticsSnapshotService()


def _snapshot_to_dict(snapshot):
    if snapshot is None:
        return {}
    if hasattr(snapshot, "to_dict"):
        return snapshot.to_dict() or {}
    if isinstance(snapshot, dict):
        return snapshot
    return {}


def _extract_before_after(event):
    data = getattr(event, "data", None)
    if data is None:
        return {}, {}

    before = _snapshot_to_dict(getattr(data, "before", None))
    after = _snapshot_to_dict(getattr(data, "after", None))

    # Fallback if runtime passes plain dict instead of change object
    if not before and not after and isinstance(data, dict):
        after = data

    return before, after


@firestore_fn.on_document_written(document="purchases/{purchaseId}", region=region)
def on_purchase_written(event: firestore_fn.Event):
    before, after = _extract_before_after(event)
    event_id = (after.get("ref_id") or before.get("ref_id") or "").strip()
    if not event_id:
        return

    logger.info("on_purchase_written: enqueue event snapshot rebuild event_id=%s", event_id)
    analytics_snapshot_service.enqueue_event_rebuild(event_id, reason="purchase_written")


@firestore_fn.on_document_written(
    document="participants/{eventId}/participants_event/{participantId}",
    region=region,
)
def on_participant_written(event: firestore_fn.Event):
    event_id = (event.params or {}).get("eventId") if hasattr(event, "params") else None
    if not event_id:
        return

    logger.info("on_participant_written: enqueue event snapshot rebuild event_id=%s", event_id)
    analytics_snapshot_service.enqueue_event_rebuild(event_id, reason="participant_written")


@firestore_fn.on_document_written(
    document="entrance_scans/{eventId}/scans/{membershipId}",
    region=region,
)
def on_entrance_scan_written(event: firestore_fn.Event):
    event_id = (event.params or {}).get("eventId") if hasattr(event, "params") else None
    if not event_id:
        return

    logger.info("on_entrance_scan_written: enqueue event snapshot rebuild event_id=%s", event_id)
    analytics_snapshot_service.enqueue_event_rebuild(event_id, reason="entrance_scan_written")


@firestore_fn.on_document_written(document="memberships/{membershipId}", region=region)
def on_membership_written(event: firestore_fn.Event):
    logger.info("on_membership_written: enqueue global snapshot rebuild")
    analytics_snapshot_service.enqueue_global_rebuild(reason="membership_written")


@scheduler_fn.on_schedule(schedule="15 5 * * *", timezone="Europe/Rome")
def rebuild_analytics_nightly(event: scheduler_fn.ScheduledEvent):
    logger.info("rebuild_analytics_nightly: enqueue full rebuild")
    analytics_snapshot_service.enqueue_full_rebuild(reason="scheduled_full_rebuild")
