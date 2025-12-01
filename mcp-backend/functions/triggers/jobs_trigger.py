from firebase_functions import firestore_fn
from firebase_admin import initialize_app, firestore
from services.mail_service import gmail_send_email_template
from config.firebase_config import db, cors, bucket

# Import the LocationService so we can run the long‑running job logic in response
# to new job documents being created.
from services.admin.location_service import LocationService

# Instantiate a single service instance to reuse the worker across invocations.
location_service = LocationService()

@firestore_fn.on_document_created(document="jobs/{jobId}")
def process_send_location_job(event: firestore_fn.Event):
    """
    Firestore trigger that runs whenever a new job document is created in the
    `jobs` collection. If the job is of type `send_location`, this trigger will
    call the worker method on the LocationService to process the job. This
    trigger ensures that work happens in a Cloud Functions environment
    independently of the HTTP request that created the job.
    """
    print("[jobs_trigger] Trigger called with event:", event)
    
    # event.data is the newly created document. It can be a DocumentSnapshot or dict.
    job_data = event.data
    job_type = None
    job_status = None

    if job_data is not None:
        # When event.data is a DocumentSnapshot
        if hasattr(job_data, "to_dict"):
            job_dict = job_data.to_dict() or {}
            job_type = job_dict.get("type")
            job_status = job_dict.get("status")
        # When event.data is already a dict
        elif isinstance(job_data, dict):
            job_type = job_data.get("type")
            job_status = job_data.get("status")

    # Extract the jobId from the route parameters.
    job_id = event.params.get("jobId") if event.params else None
    
    # Debug output
    print(f"[jobs_trigger] Extracted jobId: {job_id}, type: {job_type}, status: {job_status}")

    # Only handle send_location jobs that are in a runnable state (running or queued).
    if job_id and job_type == "send_location" and job_status in ("running", "queued"):
        print(f"[jobs_trigger] Processing job {job_id} (status={job_status})")
        # Delegate the actual work to the LocationService. This method updates
        # the job document's progress while sending the emails.
        location_service._worker_send_location(job_id)
    else:
        print(f"[jobs_trigger] Ignoring job {job_id}: unsuitable type/status")