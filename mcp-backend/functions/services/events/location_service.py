import logging
import random
import time
from dataclasses import replace
from typing import List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import transactional as _fs_transactional

from config.firebase_config import db
from config.location_config import (
    LOCATION_BASE_DELAY,
    LOCATION_MAX_DELAY,
    LOCATION_MAX_RETRIES,
    LOCATION_MIN_INTERVAL,
)
from dto.participant_api import (
    LocationActionResponseDTO,
    LocationBulkActionResponseDTO,
    LocationJobResponseDTO,
    SendLocationRequestDTO,
    SendLocationToAllRequestDTO,
)
from errors.service_errors import ExternalServiceError, NotFoundError, ValidationError
from interfaces.repositories import (
    EventRepositoryProtocol,
    JobRepositoryProtocol,
    ParticipantRepositoryProtocol,
)
from mappers.participant_mappers import mark_participant_location_sent
from models import Event, EventParticipant, Job
from repositories import EventRepository, ParticipantRepository
from repositories.job_repository import JobRepository
from services.communications.mail_service import EmailMessage, MailService, mail_service
from utils.templates_mail import build_location_email_payload


logger = logging.getLogger("LocationService")


@_fs_transactional
def _claim_job(transaction, job_ref):
    snap = job_ref.get(transaction=transaction)
    if not snap.exists:
        return False
    status = (snap.to_dict() or {}).get("status")
    if status != "queued":
        return False
    transaction.update(job_ref, {"status": "running"})
    return True


def _sleep_with_jitter(seconds: float) -> None:
    jitter = seconds * (0.8 + 0.4 * random.random())
    time.sleep(jitter)


def _send_with_retry(
    email: str,
    subject: str,
    text: str,
    html: str,
    mail_service_instance: MailService,
) -> bool:
    delay = LOCATION_BASE_DELAY
    for attempt in range(1, LOCATION_MAX_RETRIES + 1):
        try:
            ok = mail_service_instance.send(
                EmailMessage(
                    to_email=email,
                    subject=subject,
                    text_content=text,
                    html_content=html,
                    category="location",
                )
            )
            if ok:
                return True
            logger.warning("Send returned False for %s (attempt %s)", email, attempt)
        except Exception as exc:
            msg = str(exc).lower()
            transient = any(
                token in msg
                for token in (
                    "429",
                    "ratelimit",
                    "quota",
                    "userrateratexceeded",
                    "backenderror",
                    "internalerror",
                    "retry-after",
                )
            )
            if not transient:
                logger.warning("Non-retriable error for %s: %s", email, exc)
                return False
            logger.warning("Transient error for %s, retry %s: %s", email, attempt, exc)

        if attempt < LOCATION_MAX_RETRIES:
            _sleep_with_jitter(delay)
            delay = min(delay * 2, LOCATION_MAX_DELAY)
    return False


class LocationService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        job_repository: Optional[JobRepositoryProtocol] = None,
        mail_service_instance: Optional[MailService] = None,
    ) -> None:
        self.event_repository = event_repository or EventRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.job_repository = job_repository or JobRepository()
        self.mail_service = mail_service_instance or mail_service

    def _load_event_model(self, event_id: str) -> Event:
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError(f"Event {event_id} not found")
        return event_model

    def _pending_participants(self, event_id: str) -> List[EventParticipant]:
        return [
            participant
            for participant in self.participant_repository.stream(event_id)
            if participant.location_sent is not True
        ]

    def _mark_location_sent(
        self,
        event_id: str,
        participant: EventParticipant,
        *,
        job_id: str | None = None,
    ) -> None:
        if not participant.id:
            return
        updated_participant = mark_participant_location_sent(
            participant,
            sent_at=firestore.SERVER_TIMESTAMP,
            job_id=job_id,
        )
        self.participant_repository.update_from_model(
            event_id,
            participant.id,
            updated_participant,
        )

    def _update_job(self, job_id: str, job: Job, **changes) -> Job:
        self.job_repository.update(job_id, changes)
        return replace(job, **changes)

    def send_location(self, dto: SendLocationRequestDTO) -> LocationActionResponseDTO:
        event_model = self._load_event_model(dto.event_id)

        participant = self.participant_repository.get(dto.event_id, dto.participant_id)
        if not participant:
            raise NotFoundError(f"Participant {dto.participant_id} not found")

        if not participant.email:
            raise ValidationError("Missing participant email")

        name = participant.name or "Partecipante"
        subject, text_content, html_content = build_location_email_payload(
            name,
            event_model,
            dto.address,
            dto.link,
            dto.message,
        )

        sent = self.mail_service.send(
            EmailMessage(
                to_email=participant.email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                category="location",
            )
        )
        if not sent:
            raise ExternalServiceError("Errore invio email")

        self._mark_location_sent(dto.event_id, participant)
        return LocationActionResponseDTO(message="Location inviata con successo")

    def start_send_location_job(
        self,
        dto: SendLocationToAllRequestDTO,
    ) -> LocationJobResponseDTO:
        event_model = self._load_event_model(dto.event_id)

        remaining = sum(
            1
            for participant in self.participant_repository.stream(dto.event_id)
            if participant.email and not participant.location_sent
        )

        job = Job(
            type="send_location",
            event_id=event_model.id or dto.event_id,
            status="queued",
            address=dto.address,
            link=dto.link,
            message=dto.message,
            total=remaining,
            sent=0,
            failed=0,
            percent=0,
            created_at=firestore.SERVER_TIMESTAMP,
        )
        job_id = self.job_repository.create_from_model(job)

        return LocationJobResponseDTO(
            message="Job queued",
            job_id=job_id,
            total=remaining,
            status="queued",
        )

    def _worker_send_location(self, job_id: str):
        job: Optional[Job] = None
        try:
            logger.info("[LocationService] Avvio worker per job %s", job_id)

            job_ref = db.collection("jobs").document(job_id)
            claimed = _claim_job(db.transaction(), job_ref)
            if not claimed:
                logger.info(
                    "[LocationService] Job %s non rivendicato (già in esecuzione o stato non processabile), skip",
                    job_id,
                )
                return

            job = self.job_repository.get_model(job_id)
            if not job:
                logger.warning("[LocationService] Job %s non trovato.", job_id)
                return

            if not job.event_id:
                self._update_job(job_id, job, status="failed", error="Missing event_id")
                return

            event_model = self._load_event_model(job.event_id)
            logger.info("[LocationService] Job per evento %s: %s", job.event_id, event_model.title)

            participants = self._pending_participants(job.event_id)
            total = len(participants)
            if job.total != total:
                job = self._update_job(job_id, job, total=total)

            sent = 0
            failed = 0
            last_send_ts = 0.0

            for idx, participant in enumerate(participants, start=1):
                email = participant.email
                name = participant.name or "Partecipante"
                logger.info("[LocationService] (%s/%s) Invio a %s…", idx, total, email)

                if not email:
                    failed += 1
                else:
                    subject, text, html = build_location_email_payload(
                        name,
                        event_model,
                        job.address,
                        job.link,
                        job.message,
                    )

                    now = time.monotonic()
                    elapsed = now - last_send_ts
                    if elapsed < LOCATION_MIN_INTERVAL:
                        time.sleep(LOCATION_MIN_INTERVAL - elapsed)

                    ok = _send_with_retry(email, subject, text, html, self.mail_service)
                    last_send_ts = time.monotonic()

                    if ok:
                        self._mark_location_sent(job.event_id, participant, job_id=job_id)
                        sent += 1
                    else:
                        failed += 1

                percent = int(((sent + failed) / max(total, 1)) * 100)
                job = self._update_job(
                    job_id,
                    job,
                    sent=sent,
                    failed=failed,
                    percent=percent,
                )

            self._update_job(job_id, job, status="completed")
            logger.info(
                "[LocationService] Job %s completato. Inviati=%s, errori=%s",
                job_id,
                sent,
                failed,
            )

        except Exception as exc:
            logger.exception("[LocationService] Errore in worker per job %s: %s", job_id, exc)
            failed_job = job or self.job_repository.get_model(job_id)
            if failed_job:
                self._update_job(job_id, failed_job, status="failed", error=str(exc))

    def send_location_to_all(
        self,
        dto: SendLocationToAllRequestDTO,
    ) -> LocationBulkActionResponseDTO:
        event_model = self._load_event_model(dto.event_id)

        success_count = 0
        fail_count = 0
        for participant in self._pending_participants(dto.event_id):
            email = participant.email
            name = participant.name or "Partecipante"
            if not email:
                fail_count += 1
                continue

            subject, text_content, html_content = build_location_email_payload(
                name,
                event_model,
                dto.address,
                dto.link,
                dto.message,
            )
            sent = self.mail_service.send(
                EmailMessage(
                    to_email=email,
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content,
                    category="location",
                )
            )

            if sent:
                self._mark_location_sent(dto.event_id, participant)
                success_count += 1
            else:
                fail_count += 1

        return LocationBulkActionResponseDTO(
            message="Location inviata",
            success=success_count,
            failures=fail_count,
        )
