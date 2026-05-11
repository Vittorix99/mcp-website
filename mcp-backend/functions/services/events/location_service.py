import logging
import random
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from google.cloud import firestore

from config.location_config import (
    LOCATION_BASE_DELAY,
    LOCATION_MAX_DELAY,
    LOCATION_MAX_RETRIES,
    LOCATION_MIN_INTERVAL,
)
from dto.location_api import (
    AdminEventLocationResponseDTO,
    GetEventLocationQueryDTO,
    MemberEventLocationResponseDTO,
    ToggleLocationPublishedRequestDTO,
    UpdateEventLocationRequestDTO,
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
from models import Event, EventParticipant, LocationJob
from models.event_location import EventLocation
from repositories import EventRepository, ParticipantRepository
from repositories.event_location_repository import EventLocationRepository
from repositories.job_repository import LOCATION_JOBS_COLLECTION, LocationJobRepository
from services.communications.mail_service import EmailMessage, MailService, mail_service
from utils.templates_mail import build_location_email_payload
from utils.safe_logging import mask_email, redact_sensitive


logger = logging.getLogger("LocationService")
LOCATION_JOB_TYPE = "send_location"
LOCATION_JOB_STALE_AFTER = timedelta(hours=1)


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
            logger.warning("Send returned False for %s (attempt %s)", mask_email(email), attempt)
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
                logger.warning("Non-retriable error for %s: %s", mask_email(email), redact_sensitive(str(exc)))
                return False
            logger.warning("Transient error for %s, retry %s: %s", mask_email(email), attempt, redact_sensitive(str(exc)))

        if attempt < LOCATION_MAX_RETRIES:
            _sleep_with_jitter(delay)
            delay = min(delay * 2, LOCATION_MAX_DELAY)
    return False


class LocationService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        job_repository: Optional[JobRepositoryProtocol[LocationJob]] = None,
        mail_service_instance: Optional[MailService] = None,
        location_event_repository: Optional[EventLocationRepository] = None,
    ) -> None:
        self.event_repository = event_repository or EventRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.job_repository = job_repository or LocationJobRepository()
        self.mail_service = mail_service_instance or mail_service
        self.location_event_repository = location_event_repository or EventLocationRepository()

    def _load_event_model(self, event_id: str) -> Event:
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError(f"Event {event_id} not found")
        return event_model

    def _load_location(self, event_id: str) -> EventLocation:
        location = self.location_event_repository.get(event_id)
        return location or EventLocation()

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

    def _update_job(self, job_id: str, job: LocationJob, **changes) -> LocationJob:
        if "updated_at" not in changes:
            changes = {"updated_at": datetime.now(timezone.utc), **changes}
        self.job_repository.update(job_id, changes)
        model_changes = {key: value for key, value in changes.items() if hasattr(job, key)}
        return replace(job, **model_changes)

    def _is_stale_job(self, payload: Dict[str, Any], now: datetime) -> bool:
        marker = self._to_datetime(payload.get("updated_at")) or self._to_datetime(payload.get("created_at"))
        if marker is None:
            return True
        return now - marker > LOCATION_JOB_STALE_AFTER

    @staticmethod
    def _to_datetime(value: Any) -> Optional[datetime]:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    # ── Admin location management ──────────────────────────────────────────────

    def get_admin_location(self, dto: GetEventLocationQueryDTO) -> AdminEventLocationResponseDTO:
        self._load_event_model(dto.event_id)
        location = self._load_location(dto.event_id)
        return AdminEventLocationResponseDTO(
            label=location.label,
            maps_url=location.maps_url,
            maps_embed_url=location.maps_embed_url,
            address=location.address,
            message=location.message,
            published=location.published,
        )

    def update_location(self, dto: UpdateEventLocationRequestDTO) -> AdminEventLocationResponseDTO:
        self._load_event_model(dto.event_id)
        location = EventLocation(
            label=dto.label,
            maps_url=dto.maps_url,
            maps_embed_url=dto.maps_embed_url,
            address=dto.address,
            message=dto.message,
        )
        self.location_event_repository.upsert_all(dto.event_id, location)
        logger.info("update_location: saved for event %s", dto.event_id)
        existing = self._load_location(dto.event_id)
        return AdminEventLocationResponseDTO(
            label=dto.label,
            maps_url=dto.maps_url,
            maps_embed_url=dto.maps_embed_url,
            address=dto.address,
            message=dto.message,
            published=existing.published,
        )

    def set_location_published(self, dto: ToggleLocationPublishedRequestDTO) -> None:
        self._load_event_model(dto.event_id)
        self.location_event_repository.set_published(dto.event_id, dto.published)
        logger.info("set_location_published: event %s published=%s", dto.event_id, dto.published)

    # ── Member location access ─────────────────────────────────────────────────

    def get_member_location(self, event_id: str) -> MemberEventLocationResponseDTO:
        event_model = self._load_event_model(event_id)
        location = self._load_location(event_id)
        if not location.published:
            raise NotFoundError("Location not available")
        return MemberEventLocationResponseDTO(
            label=location.label,
            maps_url=location.maps_url,
            maps_embed_url=location.maps_embed_url,
            address=location.address,
            message=location.message,
            hint=event_model.location_hint or "",
        )

    # ── Email sending ──────────────────────────────────────────────────────────

    def send_location(self, dto: SendLocationRequestDTO) -> LocationActionResponseDTO:
        event_model = self._load_event_model(dto.event_id)

        participant = self.participant_repository.get(dto.event_id, dto.participant_id)
        if not participant:
            raise NotFoundError(f"Participant {dto.participant_id} not found")

        if not participant.email:
            raise ValidationError("Missing participant email")

        stored_location = self._load_location(dto.event_id)
        label = stored_location.label or ""
        address = dto.address or stored_location.address or ""
        link = dto.link or stored_location.maps_url or ""
        message = dto.message or stored_location.message or None

        name = participant.name or "Partecipante"
        subject, text_content, html_content = build_location_email_payload(
            name,
            event_model,
            label,
            address,
            link,
            message,
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

        try:
            if address or link:
                self.location_event_repository.merge_address(dto.event_id, address, link)
        except Exception as exc:
            logger.warning("send_location: event_locations write failed: %s", redact_sensitive(str(exc)))

        return LocationActionResponseDTO(message="Location inviata con successo")

    def start_send_location_job(
        self,
        dto: SendLocationToAllRequestDTO,
    ) -> LocationJobResponseDTO:
        event_model = self._load_event_model(dto.event_id)

        stored_location = self._load_location(dto.event_id)
        address = dto.address or stored_location.address or ""
        link = dto.link or stored_location.maps_url or ""
        message = dto.message or stored_location.message or None

        remaining = sum(
            1
            for participant in self.participant_repository.stream(dto.event_id)
            if participant.email and not participant.location_sent
        )
        event_id = event_model.id or dto.event_id
        now = datetime.now(timezone.utc)

        for doc_id, payload in self.job_repository.stream_raw_by_type(LOCATION_JOB_TYPE):
            status = str(payload.get("status") or "").lower()
            if status not in {"queued", "running"}:
                continue
            if (payload.get("event_id") or "") != event_id:
                continue

            if status == "queued":
                self.job_repository.update(
                    doc_id,
                    {
                        "address": address,
                        "link": link,
                        "message": message,
                        "total": remaining,
                        "error": None,
                        "updated_at": now,
                        "last_kicked_at": now,
                    },
                )
                try:
                    if address or link:
                        self.location_event_repository.merge_address(event_id, address, link)
                except Exception as exc:
                    logger.warning("start_send_location_job: event_locations write failed: %s", redact_sensitive(str(exc)))
                return LocationJobResponseDTO(
                    message="Job queued",
                    job_id=doc_id,
                    job_collection=LOCATION_JOBS_COLLECTION,
                    total=remaining,
                    status="queued",
                )

            if self._is_stale_job(payload, now):
                self.job_repository.update(
                    doc_id,
                    {
                        "status": "failed",
                        "error": "Stale location job superseded by a new request",
                        "finished_at": now,
                        "updated_at": now,
                    },
                )
                continue

            return LocationJobResponseDTO(
                message="Job already running",
                job_id=doc_id,
                job_collection=LOCATION_JOBS_COLLECTION,
                total=int(payload.get("total") or remaining),
                status="running",
            )

        job = LocationJob(
            event_id=event_id,
            status="queued",
            address=address,
            link=link,
            message=message,
            total=remaining,
            sent=0,
            failed=0,
            percent=0,
            created_at=firestore.SERVER_TIMESTAMP,
            updated_at=now,
        )
        job_id = self.job_repository.create_from_model(job)

        try:
            if address or link:
                self.location_event_repository.merge_address(event_id, address, link)
        except Exception as exc:
            logger.warning("start_send_location_job: event_locations write failed: %s", redact_sensitive(str(exc)))

        return LocationJobResponseDTO(
            message="Job queued",
            job_id=job_id,
            job_collection=LOCATION_JOBS_COLLECTION,
            total=remaining,
            status="queued",
        )

    def _worker_send_location(self, job_id: str):
        job: Optional[LocationJob] = None
        try:
            logger.info("[LocationService] Avvio worker per job %s", job_id)

            claimed = self.job_repository.claim_queued(job_id)
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

            stored_location = self._load_location(job.event_id)
            job_label = stored_location.label or ""

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
                logger.info("[LocationService] (%s/%s) Invio a %s", idx, total, mask_email(email))

                if not email:
                    failed += 1
                else:
                    subject, text, html = build_location_email_payload(
                        name,
                        event_model,
                        job_label,
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
            logger.error("[LocationService] Errore in worker per job %s: %s", job_id, redact_sensitive(str(exc)))
            failed_job = job or self.job_repository.get_model(job_id)
            if failed_job:
                self._update_job(job_id, failed_job, status="failed", error=str(exc))

    def send_location_to_all(
        self,
        dto: SendLocationToAllRequestDTO,
    ) -> LocationBulkActionResponseDTO:
        event_model = self._load_event_model(dto.event_id)

        stored_location = self._load_location(dto.event_id)
        label = stored_location.label or ""
        address = dto.address or stored_location.address or ""
        link = dto.link or stored_location.maps_url or ""
        message = dto.message or stored_location.message or None

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
                label,
                address,
                link,
                message,
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
