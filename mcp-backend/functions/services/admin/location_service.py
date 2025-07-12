import logging
from config.firebase_config import db
from utils.email_templates import get_location_email_template
from services.mail_service import gmail_send_email_template

logger = logging.getLogger('LocationService')

class LocationService:
    def send_location(self, event_id, participant_id, address=None, link=None):
        try:
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

            subject = f"Location per l'evento {event_data.get('title')}"
            html_content = get_location_email_template(name, event_data, address, link)
            text_content = f"""
Ciao {name},

Ecco i dettagli della location per l'evento "{event_data.get("title")}":

Data: {event_data.get("date")}
Orario: {event_data.get("startTime")} - {event_data.get("endTime")}
{f"Indirizzo: {address}" if address else ""}
{f"Link: {link}" if link else ""}

A presto!
"""

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

    def send_location_to_all(self, event_id, address=None, link=None):
        try:
            if not event_id:
                return {'error': 'Missing eventId'}, 400

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
                email = data.get("email")
                name = data.get("name", "Partecipante")

                subject = f"Location per l'evento {event_data.get('title')}"
                html_content = get_location_email_template(name, event_data, address, link)
                text_content = f"""
Ciao {name},

Ecco i dettagli della location per l'evento "{event_data.get("title")}":

Data: {event_data.get("date")}
Orario: {event_data.get("startTime")} - {event_data.get("endTime")}
{f"Indirizzo: {address}" if address else ""}
{f"Link: {link}" if link else ""}

A presto!
"""

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