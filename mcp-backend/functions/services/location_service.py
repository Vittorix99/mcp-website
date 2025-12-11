from config.firebase_config import db
from utils.email_templates import get_location_email_template
from services.mail_service import gmail_send_email_template
from google.cloud import firestore
import threading
import time, random, logging



logger = logging.getLogger('LocationService')
# Parametri di throttling / retry
MIN_INTERVAL = 0.8       # secondi minimi tra invii (~120/min)
MAX_RETRIES = 5
BASE_DELAY = 1.0         # 1s primo retry
MAX_DELAY = 30.0         # max 30s attesa


def _sleep_with_jitter(seconds: float):
    jitter = seconds * (0.8 + 0.4 * random.random())
    time.sleep(jitter)

def _send_with_retry(email, subject, text, html):
    delay = BASE_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ok = gmail_send_email_template(email, subject, text, html)
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
                logger.warning(f"Non-retriable error for {email}: {e}")
                return False
            logger.warning(f"Transient error for {email}, retry {attempt}: {e}")

        if attempt < MAX_RETRIES:
            _sleep_with_jitter(delay)
            delay = min(delay * 2, MAX_DELAY)
    return False

def _build_location_email_payload(name, event_dict, address=None, link=None, message=None):
    subject = f"Location per l'evento {event_dict.get('title')}"
    html_content = get_location_email_template(name, event_dict, address, link)
    if message:
        html_content = (
            html_content
            + f"""
<hr style=\"margin:16px 0; border:none; border-top:1px solid #e5e5e5;\" />
<p style=\"margin:0;\"><strong>Messaggio dagli organizzatori:</strong></p>
<p style=\"white-space:pre-wrap; margin-top:4px;\">{message}</p>
"""
        )
    text_content = f"""
Ciao {name},

Ecco i dettagli della location per l'evento \"{event_dict.get("title")}\":

Data: {event_dict.get("date")}
Orario: {event_dict.get("startTime")} - {event_dict.get("endTime")}
{f"Indirizzo: {address}" if address else ""}
{f"Link: {link}" if link else ""}
"""
    if message:
        text_content += f"\n\nMessaggio dagli organizzatori:\n{message}"
    text_content += "\n\nA presto!\n"
    return subject, text_content, html_content

class LocationService:
    def send_location(self, event_id, participant_id, address=None, link=None, message=None):
        try:
            # sanitize optional fields
            address = (address or "").strip() or None
            link = (link or "").strip() or None
            message = (message or "").strip() or None

            if not event_id or not participant_id:
                return {'error': 'Missing eventId or participantId'}, 400

            event_ref = db.collection("events").document(event_id).get()
            if not event_ref.exists:
                return {'error': f"Event {event_id} not found"}, 404
            event_data = event_ref.to_dict()

            participant_ref = db.collection("participants") \
                .document(event_id).collection("participants_event") \
                .document(participant_id).get()

            if not participant_ref.exists:
                return {'error': f"Participant {participant_id} not found"}, 404

            participant_data = participant_ref.to_dict()
            name = participant_data.get("name", "Partecipante")
            email = participant_data.get("email")

            subject, text_content, html_content = _build_location_email_payload(
                name,
                event_data,
                address,
                link,
                message,
            )

            sent = gmail_send_email_template(email, subject, text_content, html_content)

            if sent:
                db.collection("participants").document(event_id) \
                    .collection("participants_event").document(participant_id) \
                    .update({"location_sent": True})
                return {'message': 'Location inviata con successo'}, 200

            return {'error': 'Errore invio email'}, 500

        except Exception as e:
            logger.exception(f"Error sending location: {e}")
            return {'error': 'Internal server error'}, 500

    
    def start_send_location_job(self, event_id, address=None, link=None, message=None):
        try:
            if not event_id:
                return {'error': 'Missing eventId'}, 400

            # sanitize optional fields
            address = (address or "").strip() or None
            link = (link or "").strip() or None
            message = (message or "").strip() or None

            # check evento
            event_ref = db.collection("events").document(event_id).get()
            if not event_ref.exists:
                return {'error': f"Event {event_id} not found"}, 404

            # conta quanti partecipanti ancora da inviare
            participants_ref = db.collection("participants").document(event_id).collection("participants_event")
            remaining = 0
            for p in participants_ref.stream():
                d = p.to_dict()
                if d.get("email") and not d.get("location_sent"):
                    remaining += 1

            # crea job doc
            job_ref = db.collection("jobs").document()
            job_ref.set({
                "type": "send_location",
                "event_id": event_id,
                "status": "queued",   # il trigger prenderà in carico il job
                "address": address,
                "link": link,
                "message": message,
                "total": remaining,
                "sent": 0,
                "failed": 0,
                "percent": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
            })

            return {
                'message': 'Job queued',
                'jobId': job_ref.id,
                'total': remaining,
                'status': 'queued'
            }, 202

        except Exception as e:
            logger.exception(f"Error creating job: {e}")
            return {'error': 'Internal server error'}, 500
        
    def _worker_send_location(self, job_id: str):
        """
        Elabora un job di tipo 'send_location', inviando email ai partecipanti che non hanno ancora ricevuto la location.
        Aggiorna lo stato del job e i contatori di progresso a ogni invio.
        """
        try:
            print(f"[LocationService] Avvio worker per job {job_id}")
            job_ref = db.collection("jobs").document(job_id)
            job_snap = job_ref.get()
            if not job_snap.exists:
                print(f"[LocationService] Job {job_id} non trovato.")
                return

            job = job_snap.to_dict() or {}
            event_id = job.get("event_id")
            if not event_id:
                print(f"[LocationService] Il job {job_id} non contiene un event_id valido.")
                job_ref.update({"status": "failed", "error": "Missing event_id"})
                return

            # Recupera dati dell'evento
            event_snap = db.collection("events").document(event_id).get()
            if not event_snap.exists:
                print(f"[LocationService] Evento {event_id} non trovato.")
                job_ref.update({"status": "failed", "error": f"Evento {event_id} missing"})
                return

            ev = event_snap.to_dict() or {}
            print(f"[LocationService] Job per evento {event_id}: {ev.get('title')}")

            # Recupera tutti i partecipanti che non hanno ancora ricevuto la location
            participants_ref = (
                db.collection("participants")
                .document(event_id)
                .collection("participants_event")
            )

            participants = []
            for doc in participants_ref.stream():
                data = doc.to_dict() or {}
                # se il campo location_sent è presente e True, salta
                if data.get("location_sent") is True:
                    continue
                participants.append(doc)
            print(f"[LocationService] Partecipanti da notificare: {len(participants)}")

            # Aggiorna eventualmente il totale se diverso
            total = job.get("total", len(participants))
            if total != len(participants):
                print(f"[LocationService] Aggiorno totale job (da {total} a {len(participants)})")
                total = len(participants)
                job_ref.update({"total": total})

            sent = 0
            failed = 0
            last_send_ts = 0.0

            # Itera sui partecipanti e invia email
            for idx, p in enumerate(participants, start=1):
                data = p.to_dict()
                email = data.get("email")
                name = data.get("name", "Partecipante")
                print(f"[LocationService] ({idx}/{len(participants)}) Invio a {email}…")

                if not email:
                    failed += 1
                    print(f"[LocationService] Nessuna email per {name}, incremento failed a {failed}")
                    continue

                # Costruisce subject, testo e html
                subject, text, html = _build_location_email_payload(
                    name,
                    ev,
                    job.get("address"),
                    job.get("link"),
                    job.get("message"),
                )

                # Throttling: rispetta MIN_INTERVAL tra invii
                now = time.monotonic()
                elapsed = now - last_send_ts
                if elapsed < MIN_INTERVAL:
                    time.sleep(MIN_INTERVAL - elapsed)

                # Invio con retry
                ok = _send_with_retry(email, subject, text, html)
                last_send_ts = time.monotonic()

                if ok:
                    # Aggiorna il partecipante
                    p.reference.update({
                        "location_sent": True,
                        "location_job_id": job_id,
                        "location_sent_at": firestore.SERVER_TIMESTAMP
                    })
                    sent += 1
                else:
                    failed += 1
                # Aggiorna la progress del job
                percent = int(((sent + failed) / max(total, 1)) * 100)
                job_ref.update({
                    "sent": sent,
                    "failed": failed,
                    "percent": percent
                })
                print(f"[LocationService] Progress job {job_id}: sent={sent}, failed={failed}, percent={percent}%")

            # Fine invio: aggiorna lo status
            job_ref.update({"status": "completed"})
            print(f"[LocationService] Job {job_id} completato. Inviati={sent}, errori={failed}")

        except Exception as e:
            # Log e aggiornamento status in caso di crash
            print(f"[LocationService] Errore in worker per job {job_id}: {e}")
            job_ref.update({
                "status": "failed",
                "error": str(e)
            })
        
        
        
         
    
    def send_location_to_all(self, event_id, address=None, link=None, message=None):
        try:
            if not event_id:
                return {'error': 'Missing eventId'}, 400

            # sanitize optional fields
            address = (address or "").strip() or None
            link = (link or "").strip() or None
            message = (message or "").strip() or None

            event_ref = db.collection("events").document(event_id).get()
            if not event_ref.exists:
                return {'error': f"Event {event_id} not found"}, 404
            event_data = event_ref.to_dict()

            participants = db.collection("participants") \
                .document(event_id).collection("participants_event").stream()

            success_count = 0
            fail_count = 0

            for p in participants:
                data = p.to_dict()

                # ⚠️ Salta se location_sent è già True
                if data.get("location_sent") is True:
                    continue

                email = data.get("email")
                name = data.get("name", "Partecipante")

                subject, text_content, html_content = _build_location_email_payload(
                    name,
                    event_data,
                    address,
                    link,
                    message,
                )

                sent = gmail_send_email_template(email, subject, text_content, html_content)

                if sent:
                    db.collection("participants").document(event_id) \
                        .collection("participants_event") \
                        .document(p.id).update({"location_sent": True})
                    success_count += 1
                else:
                    fail_count += 1

            return {
                'message': 'Location inviata',
                'success': success_count,
                'failures': fail_count
            }, 200

        except Exception as e:
            logger.exception(f"Error sending location to all: {e}")
            return {'error': 'Internal server error'}, 500
