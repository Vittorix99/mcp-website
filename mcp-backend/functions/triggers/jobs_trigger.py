import logging

from firebase_functions import firestore_fn

from services.events.location_service import LocationService

logger = logging.getLogger("jobs_trigger")
location_service = LocationService()


@firestore_fn.on_document_created(document="jobs/{jobId}")
def process_send_location_job(event: firestore_fn.Event):
    """Trigger Firestore: avvia il worker solo per job send_location in stato eseguibile."""
    job_data = event.data
    job_type = None
    job_status = None

    if job_data is not None:
        if hasattr(job_data, "to_dict"):
            job_dict = job_data.to_dict() or {}
            job_type = job_dict.get("type")
            job_status = job_dict.get("status")
        elif isinstance(job_data, dict):
            job_type = job_data.get("type")
            job_status = job_data.get("status")

    job_id = event.params.get("jobId") if event.params else None

    logger.info(
        "process_send_location_job: jobId=%s type=%s status=%s",
        job_id, job_type, job_status,
    )

    # Il trigger e' generico sulla collection jobs: filtriamo qui il tipo di lavoro.
    if job_id and job_type == "send_location" and job_status in ("running", "queued"):
        logger.info("process_send_location_job: processing job %s", job_id)
        location_service._worker_send_location(job_id)
    else:
        logger.info(
            "process_send_location_job: skipping job %s (type=%s status=%s)",
            job_id, job_type, job_status,
        )
