import logging
import random
import time
from typing import List, Optional

from google.cloud import firestore

from config.location_config import (
    LOCATION_BASE_DELAY,
    LOCATION_MAX_DELAY,
    LOCATION_MAX_RETRIES,
    LOCATION_MIN_INTERVAL,
)
from dto import EventDTO, EventParticipantDTO, JobDTO
from models import Job
from repositories import EventRepository, ParticipantRepository
from repositories.job_repository import JobRepository
from services.mail_service import EmailMessage, mail_service
from services.service_errors import ExternalServiceError, NotFoundError, ValidationError
from utils.templates_mail import build_location_email_payload



logger = logging.getLogger('LocationService')
def _sleep_with_jitter(seconds: float) -> None:
    jitter = seconds * (0.8 + 0.4 * random.random())
    time.sleep(jitter)

def _send_with_retry(email: str, subject: str, text: str, html: str) -> bool:
    delay = LOCATION_BASE_DELAY
    for attempt in range(1, LOCATION_MAX_RETRIES + 1):
        try:
            ok = mail_service.send(
                EmailMessage(
                    to_email=email,
                    subject=subject,
                    text_content=text,
                    html_content=html,
                )
            )
            if ok:
                return True
            logger.warning(f"Send returned False for {email} (attempt {attempt})")
        except Exception as e:
            msg = str(e).lower()
            # errori "transitori": quota, rate limit, 429, ecc.
            transient = any(k in msg for k in (
                "429", "ratelimit", "quota", "userrateratexceeded",
                "backenderror", "internalerror", "retry-after"
            ))
            if not transient:
                logger.warning("Non-retriable error for %s: %s", email, e)
                return False
            logger.warning("Transient error for %s, retry %s: %s", email, attempt, e)

        if attempt < LOCATION_MAX_RETRIES:
            _sleep_with_jitter(delay)
            delay = min(delay * 2, LOCATION_MAX_DELAY)
    return False


class LocationService:
    def __init__(self) -> None:
        self.event_repository = EventRepository()
        self.participant_repository = ParticipantRepository()
        self.job_repository = JobRepository()

    def _load_event_dto(self, event_id: str) -> Optional[EventDTO]:
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            return None
        return EventDTO.from_model(event_model)

    def _pending_participants(self, event_id: str) -> List[EventParticipantDTO]:
        participants: List[EventParticipantDTO] = []
        for participant in self.participant_repository.stream(event_id):
            if participant.location_sent is True:
                continue
            participants.append(participant)
        return participants

    def send_location(self, event_id, participant_id, address=None, link=None, message=None):
        # sanitize optional fields
        address = (address or "").strip() or None
        link = (link or "").strip() or None
        message = (message or "").strip() or None

        if not event_id or not participant_id:
            raise ValidationError("Missing eventId or participantId")

        event_data = self._load_event_dto(event_id)
        if not event_data:
            raise NotFoundError(f"Event {event_id} not found")

        participant = self.participant_repository.get(event_id, participant_id)
        if not participant:
            raise NotFoundError(f"Participant {participant_id} not found")

        name = participant.name or "Partecipante"
        email = participant.email
        if not email:
            raise ValidationError("Missing participant email")

        subject, text_content, html_content = build_location_email_payload(
            name,
            event_data,
            address,
            link,
            message,
        )

        sent = mail_service.send(
            EmailMessage(
                to_email=email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
            )
        )

        if not sent:
            raise ExternalServiceError("Errore invio email")

        participant_update = EventParticipantDTO(
            location_sent=True,
            location_sent_at=firestore.SERVER_TIMESTAMP,
        )
        self.participant_repository.update(
            event_id,
            participant_id,
            participant_update,
        )
        return {"message": "Location inviata con successo"}

    
    def start_send_location_job(self, event_id, address=None, link=None, message=None):
        if not event_id:
            raise ValidationError("Missing eventId")

        # sanitize optional fields
        address = (address or "").strip() or None
        link = (link or "").strip() or None
        message = (message or "").strip() or None

        # check evento
        event_data = self._load_event_dto(event_id)
        if not event_data:
            raise NotFoundError(f"Event {event_id} not found")

        # conta quanti partecipanti ancora da inviare
        remaining = 0
        for participant in self.participant_repository.stream(event_id):
            if participant.email and not participant.location_sent:
                remaining += 1

        job = Job(
            type="send_location",
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
        )
        job_id = self.job_repository.create_from_model(job)

        return {
            "message": "Job queued",
            "jobId": job_id,
            "total": remaining,
            "status": "queued",
        }
        
    def _worker_send_location(self, job_id: str):
        """
        Elabora un job di tipo 'send_location', inviando email ai partecipanti che non hanno ancora ricevuto la location.
        Aggiorna lo stato del job e i contatori di progresso a ogni invio.
        """
        try:
            logger.info("[LocationService] Avvio worker per job %s", job_id)
            job = self.job_repository.get_model(job_id)
            if not job:
                logger.warning("[LocationService] Job %s non trovato.", job_id)
                return

            event_id = job.event_id
            if not event_id:
                logger.warning("[LocationService] Il job %s non contiene un event_id valido.", job_id)
                self.job_repository.update_from_model(
                    job_id,
                    JobDTO(status="failed", error="Missing event_id"),
                )
                return

            # Recupera dati dell'evento
            event_payload = self._load_event_dto(event_id)
            if not event_payload:
                logger.warning("[LocationService] Evento %s non trovato.", event_id)
                self.job_repository.update_from_model(
                    job_id,
                    JobDTO(status="failed", error=f"Evento {event_id} missing"),
                )
                return

            logger.info("[LocationService] Job per evento %s: %s", event_id, event_payload.title)

            # Recupera tutti i partecipanti che non hanno ancora ricevuto la location
            participants = self._pending_participants(event_id)
            logger.info("[LocationService] Partecipanti da notificare: %s", len(participants))

            # Aggiorna eventualmente il totale se diverso
            total = job.total if job.total else len(participants)
            if total != len(participants):
                logger.info("[LocationService] Aggiorno totale job (da %s a %s)", total, len(participants))
                total = len(participants)
                self.job_repository.update_from_model(job_id, JobDTO(total=total))

            sent = 0
            failed = 0
            last_send_ts = 0.0

            # Itera sui partecipanti e invia email
            for idx, participant in enumerate(participants, start=1):
                email = participant.email
                name = participant.name or "Partecipante"
                logger.info("[LocationService] (%s/%s) Invio a %s…", idx, len(participants), email)

                if not email:
                    failed += 1
                    logger.warning("[LocationService] Nessuna email per %s, incremento failed a %s", name, failed)
                    continue

                # Costruisce subject, testo e html
                subject, text, html = build_location_email_payload(
                    name,
                    event_payload,
                    job.address,
                    job.link,
                    job.message,
                )

                # Throttling: rispetta MIN_INTERVAL tra invii
                now = time.monotonic()
                elapsed = now - last_send_ts
                if elapsed < LOCATION_MIN_INTERVAL:
                    time.sleep(LOCATION_MIN_INTERVAL - elapsed)

                # Invio con retry
                ok = _send_with_retry(email, subject, text, html)
                last_send_ts = time.monotonic()

                if ok:
                    # Aggiorna il partecipante
                    if participant.id:
                        participant_update = EventParticipantDTO(
                            location_sent=True,
                            location_job_id=job_id,
                            location_sent_at=firestore.SERVER_TIMESTAMP,
                        )
                        self.participant_repository.update(
                            event_id,
                            participant.id,
                            participant_update,
                        )
                    sent += 1
                else:
                    failed += 1
                # Aggiorna la progress del job
                percent = int(((sent + failed) / max(total, 1)) * 100)
                self.job_repository.update_from_model(
                    job_id,
                    JobDTO(
                        sent=sent,
                        failed=failed,
                        percent=percent,
                    ),
                )
                logger.info(
                    "[LocationService] Progress job %s: sent=%s, failed=%s, percent=%s%%",
                    job_id,
                    sent,
                    failed,
                    percent,
                )

            # Fine invio: aggiorna lo status
            self.job_repository.update_from_model(job_id, JobDTO(status="completed"))
            logger.info("[LocationService] Job %s completato. Inviati=%s, errori=%s", job_id, sent, failed)

        except Exception as e:
            # Log e aggiornamento status in caso di crash
            logger.exception("[LocationService] Errore in worker per job %s: %s", job_id, e)
            self.job_repository.update_from_model(
                job_id,
                JobDTO(status="failed", error=str(e)),
            )
        
        
        
         
    
    def send_location_to_all(self, event_id, address=None, link=None, message=None):
        if not event_id:
            raise ValidationError("Missing eventId")

        # sanitize optional fields
        address = (address or "").strip() or None
        link = (link or "").strip() or None
        message = (message or "").strip() or None

        event_data = self._load_event_dto(event_id)
        if not event_data:
            raise NotFoundError(f"Event {event_id} not found")

        success_count = 0
        fail_count = 0

        for participant in self._pending_participants(event_id):
            email = participant.email
            name = participant.name or "Partecipante"
            if not email:
                fail_count += 1
                continue

            subject, text_content, html_content = build_location_email_payload(
                name,
                event_data,
                address,
                link,
                message,
            )

            sent = mail_service.send(
                EmailMessage(
                    to_email=email,
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content,
                )
            )

            if sent:
                if participant.id:
                    participant_update = EventParticipantDTO(
                        location_sent=True,
                        location_sent_at=firestore.SERVER_TIMESTAMP,
                    )
                    self.participant_repository.update(
                        event_id,
                        participant.id,
                        participant_update,
                    )
                success_count += 1
            else:
                fail_count += 1

        return {
            "message": "Location inviata",
            "success": success_count,
            "failures": fail_count,
        }
