import logging

from firebase_functions import firestore_fn

from config.firebase_config import region
from services.events.location_service import LocationService
from services.core.analytics_snapshot_service import AnalyticsSnapshotService

logger = logging.getLogger("jobs_trigger")
location_service = LocationService()
analytics_snapshot_service = AnalyticsSnapshotService()


def _snapshot_to_dict(snapshot):
    if snapshot is None:
        return {}
    if hasattr(snapshot, "to_dict"):
        return snapshot.to_dict() or {}
    if isinstance(snapshot, dict):
        return snapshot
    return {}


def _event_after_data(event):
    data = getattr(event, "data", None)
    after = getattr(data, "after", None)
    if after is not None:
        return _snapshot_to_dict(after)
    return _snapshot_to_dict(data)


@firestore_fn.on_document_written(document="location_jobs/{jobId}", region=region)
def process_send_location_job(event: firestore_fn.Event):
    """Trigger Firestore: avvia il worker per job location queued in location_jobs."""
    job_dict = _event_after_data(event)
    job_type = job_dict.get("type")
    job_status = job_dict.get("status")

    job_id = event.params.get("jobId") if event.params else None

    logger.info(
        "process_send_location_job: jobId=%s type=%s status=%s",
        job_id, job_type, job_status,
    )

    if job_id and job_type == "send_location" and job_status == "queued":
        logger.info("process_send_location_job: processing job %s", job_id)
        location_service._worker_send_location(job_id)
    else:
        logger.info(
            "process_send_location_job: skipping job %s (type=%s status=%s)",
            job_id, job_type, job_status,
        )


@firestore_fn.on_document_written(document="analytics_jobs/{jobId}", region=region)
def process_analytics_rebuild_job(event: firestore_fn.Event):
    """Trigger Firestore: avvia worker analytics su create/update di analytics_jobs."""
    job_dict = _event_after_data(event)
    job_type = job_dict.get("type")
    job_status = job_dict.get("status")

    job_id = event.params.get("jobId") if event.params else None
    logger.info(
        "process_analytics_rebuild_job: jobId=%s type=%s status=%s",
        job_id,
        job_type,
        job_status,
    )

    if job_id and job_type == "analytics_rebuild" and job_status == "queued":
        logger.info("process_analytics_rebuild_job: processing job %s", job_id)
        analytics_snapshot_service.process_rebuild_job(job_id)
    else:
        logger.info(
            "process_analytics_rebuild_job: skipping job %s (type=%s status=%s)",
            job_id,
            job_type,
            job_status,
        )
