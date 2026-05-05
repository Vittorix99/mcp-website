import pytest

from api.admin import participants_api
from config.firebase_config import db
from tests.utils import DummyRequest, unwrap_response


# ---------------------------------------------------------------------------
# send_tickets_to_all API tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_send_tickets_to_all_returns_202_and_job_id(
    create_event,
    job_repository,
):
    """POST /send_tickets_to_all returns 202 with a jobId and status=queued."""
    event_id = create_event()
    job_id = None
    try:
        req = DummyRequest(method="POST", json={"eventId": event_id})
        resp, status = unwrap_response(participants_api.send_tickets_to_all(req))

        assert status == 202
        assert resp.get("status") == "queued"
        job_id = resp.get("jobId")
        assert job_id, "Response must include a jobId"

        # Confirm the job document was actually created in Firestore
        job_snap = db.collection("jobs").document(job_id).get()
        assert job_snap.exists, "Job document must exist in Firestore"
        job_data = job_snap.to_dict() or {}
        assert job_data.get("type") == "send_ticket"
        assert job_data.get("event_id") == event_id
        assert job_data.get("status") == "queued"
    finally:
        if job_id:
            db.collection("jobs").document(job_id).delete()


@pytest.mark.integration
def test_send_tickets_to_all_with_participants_reports_correct_total(
    create_event,
    create_participants_bulk,
    job_repository,
):
    """total in the 202 response matches the number of participants with an email."""
    NUM_PARTICIPANTS = 10
    event_id = create_event()
    create_participants_bulk(event_id, count=NUM_PARTICIPANTS)
    job_id = None
    try:
        req = DummyRequest(method="POST", json={"eventId": event_id})
        resp, status = unwrap_response(participants_api.send_tickets_to_all(req))

        assert status == 202
        assert resp.get("total") == NUM_PARTICIPANTS
        job_id = resp.get("jobId")
    finally:
        if job_id:
            db.collection("jobs").document(job_id).delete()


@pytest.mark.integration
def test_send_tickets_to_all_wrong_method_returns_405():
    """Non-POST requests are rejected with 405."""
    req = DummyRequest(method="GET", json={})
    resp, status = unwrap_response(participants_api.send_tickets_to_all(req))
    assert status == 405


@pytest.mark.integration
@pytest.mark.email
@pytest.mark.usefixtures("mailersend_api_key")
def test_send_tickets_to_all_full_flow_via_api_and_worker(
    ticket_service,
    create_event,
    create_participants_bulk,
    job_repository,
):
    """
    Full end-to-end flow through the API + worker:
    - POST to the API creates a queued job
    - Running the worker processes the job
    - All 10 participants receive their ticket email
    - Job is marked as completed
    """
    if ticket_service.documents_service.storage is None:
        pytest.skip("Storage bucket not configured for ticket generation")

    NUM_PARTICIPANTS = 10
    event_id = create_event()
    participant_ids = create_participants_bulk(event_id, count=NUM_PARTICIPANTS)
    job_id = None

    try:
        # Step 1: call the API endpoint
        req = DummyRequest(method="POST", json={"eventId": event_id})
        resp, status = unwrap_response(participants_api.send_tickets_to_all(req))
        assert status == 202
        job_id = resp.get("jobId")
        assert job_id

        # Step 2: run the worker (normally triggered by Firestore document creation)
        ticket_service._worker_send_tickets(job_id)

        # Step 3: verify job completed
        job_data = db.collection("jobs").document(job_id).get().to_dict() or {}
        assert job_data.get("status") == "completed", (
            f"Job ended with status={job_data.get('status')}, error={job_data.get('error')}"
        )
        assert job_data.get("sent") == NUM_PARTICIPANTS
        assert job_data.get("failed") == 0
        assert job_data.get("percent") == 100

        # Step 4: verify all participants have ticket_sent=True
        for participant_id in participant_ids:
            p_data = (
                db.collection("participants")
                .document(event_id)
                .collection("participants_event")
                .document(participant_id)
                .get()
                .to_dict()
                or {}
            )
            assert p_data.get("ticket_sent") is True, (
                f"Participant {participant_id} did not receive ticket"
            )

    finally:
        # Clean up PDFs from storage
        event_snap = db.collection("events").document(event_id).get().to_dict() or {}
        for participant_id in participant_ids:
            p_data = (
                db.collection("participants")
                .document(event_id)
                .collection("participants_event")
                .document(participant_id)
                .get()
                .to_dict()
                or {}
            )
            storage_path = ticket_service._build_storage_path(
                event_snap.get("title"),
                p_data.get("name"),
                p_data.get("surname"),
            )
            if ticket_service.documents_service.storage:
                blob = ticket_service.documents_service.storage.blob(storage_path)
                if blob.exists():
                    blob.delete()

        if job_id:
            db.collection("jobs").document(job_id).delete()
