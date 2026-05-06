from models import Event, EventParticipant, LocationJob
from dto.participant_api import SendLocationToAllRequestDTO
from repositories.job_repository import LOCATION_JOBS_COLLECTION
from services.events import location_service as location_module
from services.events.location_service import LocationService


class _EventRepo:
    def __init__(self):
        self.event = Event(id="event-1", title="Evento", date="06-05-2026", start_time="21:00", end_time="23:00")

    def get_model(self, event_id):
        return self.event if event_id == "event-1" else None


class _ParticipantRepo:
    def __init__(self, participants):
        self.participants = participants
        self.updated = []

    def stream(self, event_id):
        return iter(self.participants)

    def update_from_model(self, event_id, participant_id, participant):
        self.updated.append((event_id, participant_id, participant))


class _LocationJobRepo:
    def __init__(self, job=None):
        self.created = None
        self.job = job
        self.updates = []
        self.raw_jobs = []

    def create_from_model(self, job):
        self.created = job
        return "location-job-1"

    def claim_queued(self, job_id):
        return True

    def get_model(self, job_id):
        return self.job

    def update(self, job_id, payload):
        self.updates.append((job_id, payload))

    def stream_raw_by_type(self, job_type):
        return iter(self.raw_jobs)


class _MailService:
    def send(self, email):
        return True


def test_start_send_location_job_creates_location_job_payload():
    participants = [
        EventParticipant(id="p1", event_id="event-1", email="one@example.com", location_sent=False),
        EventParticipant(id="p2", event_id="event-1", email="", location_sent=False),
        EventParticipant(id="p3", event_id="event-1", email="done@example.com", location_sent=True),
    ]
    job_repo = _LocationJobRepo()
    service = LocationService(
        event_repository=_EventRepo(),
        participant_repository=_ParticipantRepo(participants),
        job_repository=job_repo,
        mail_service_instance=_MailService(),
    )

    result = service.start_send_location_job(
        SendLocationToAllRequestDTO(
            event_id="event-1",
            address="Via Roma",
            link="https://maps.example",
            message="Ingresso A",
        )
    )

    assert result.job_id == "location-job-1"
    assert result.job_collection == LOCATION_JOBS_COLLECTION
    assert isinstance(job_repo.created, LocationJob)
    assert job_repo.created.event_id == "event-1"
    assert job_repo.created.address == "Via Roma"
    assert job_repo.created.link == "https://maps.example"
    assert job_repo.created.message == "Ingresso A"
    assert job_repo.created.total == 1
    assert job_repo.created.sent == 0
    assert job_repo.created.failed == 0


def test_start_send_location_job_kicks_existing_queued_location_job():
    participants = [
        EventParticipant(id="p1", event_id="event-1", email="one@example.com", location_sent=False),
    ]
    job_repo = _LocationJobRepo()
    job_repo.raw_jobs = [
        ("location-job-queued", {"type": "send_location", "status": "queued", "event_id": "event-1"})
    ]
    service = LocationService(
        event_repository=_EventRepo(),
        participant_repository=_ParticipantRepo(participants),
        job_repository=job_repo,
        mail_service_instance=_MailService(),
    )

    result = service.start_send_location_job(
        SendLocationToAllRequestDTO(
            event_id="event-1",
            address="Via Milano",
            link="https://maps.example/new",
            message="Ingresso B",
        )
    )

    assert result.job_id == "location-job-queued"
    assert result.status == "queued"
    assert job_repo.created is None
    assert job_repo.updates[0][0] == "location-job-queued"
    assert job_repo.updates[0][1]["address"] == "Via Milano"
    assert job_repo.updates[0][1]["link"] == "https://maps.example/new"
    assert job_repo.updates[0][1]["message"] == "Ingresso B"
    assert job_repo.updates[0][1]["total"] == 1


def test_worker_send_location_processes_location_job(monkeypatch):
    participants = [
        EventParticipant(id="p1", event_id="event-1", name="One", email="one@example.com", location_sent=False),
        EventParticipant(id="p2", event_id="event-1", name="Two", email="", location_sent=False),
    ]
    job = LocationJob(
        event_id="event-1",
        address="Via Roma",
        link="https://maps.example",
        message="Ingresso A",
        total=0,
    )
    participant_repo = _ParticipantRepo(participants)
    job_repo = _LocationJobRepo(job=job)
    monkeypatch.setattr(location_module, "build_location_email_payload", lambda *args, **kwargs: ("subject", "text", "html"))
    monkeypatch.setattr(location_module, "_send_with_retry", lambda *args, **kwargs: True)

    service = LocationService(
        event_repository=_EventRepo(),
        participant_repository=participant_repo,
        job_repository=job_repo,
        mail_service_instance=_MailService(),
    )

    service._worker_send_location("location-job-1")

    assert participant_repo.updated[0][0] == "event-1"
    assert participant_repo.updated[0][1] == "p1"
    assert participant_repo.updated[0][2].location_job_id == "location-job-1"
    assert any(update[0] == "location-job-1" and update[1].get("status") == "completed" for update in job_repo.updates)
    assert any(update[1].get("total") == 2 for update in job_repo.updates)
    assert any(update[1].get("sent") == 1 and update[1].get("failed") == 1 for update in job_repo.updates)
