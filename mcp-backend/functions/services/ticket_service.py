from google.cloud import firestore
import os
from services.mail_service import gmail_send_email_template
from utils.email_templates import get_ticket_email_template
import sys
from datetime import datetime
from utils.pdf_template import generate_ticket_pdf
from config.firebase_config import db, bucket, cors
from config.event_types import EventTypes





def process_new_ticket(participant_id, participant_data, send=True):
    """Genera PDF, opzionalmente invia il ticket per email e aggiorna il DB. L'URL del PDF è solo per uso admin."""
    try:
        event_id = participant_data.get("event_id")
        if not event_id:
            print("⚠️ Missing event_id")
            return {"success": False, "error": "Missing event_id"}

        # 🔍 Recupera evento
        event_doc = db.collection("events").document(event_id).get()
        if not event_doc.exists:
            return {"success": False, "error": f"Event {event_id} not found"}
        event_data = event_doc.to_dict()
        print(f"📅 Evento trovato: {event_data.get('title')}")
        ev_type = (event_data.get("type") or "").lower()
        print(f"📦 Event type: {ev_type}")

        # 📄 Genera PDF
        pdf_buffer = generate_ticket_pdf(participant_data, event_data, "logos/logo_white.png")
        name = participant_data.get("name", "user")
        surname = participant_data.get("surname", "")
        name_surname = f"{name}_{surname}"
        title_event = event_data.get("title", "event")
        pdf_path = f"tickets/{title_event}/{name_surname}_ticket.pdf"

        # 📤 Salva PDF in Storage
        blob = bucket.blob(pdf_path)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_url = blob.public_url
        print(f"✅ PDF salvato (uso admin): {pdf_url}")

        update_payload = {
            "ticket_pdf_url": pdf_url,
            "ticket_sent": False  # Default, updated below if mail is sent
        }

        print("Send is:", send)
        if send:
            # 📧 Prepara contenuto email
            subject = f"🎟️ Il tuo ticket per {event_data.get('title')}"
            html_content = get_ticket_email_template(participant_data, event_data)
            text_content = f"""
Grazie per la tua partecipazione!

Evento: {event_data.get('title')}
Data: {event_data.get('date')}
Location: {event_data.get('location')}

Dettagli:
- Nome: {name} 
- Cognome: {surname}

Troverai il tuo biglietto in allegato a questa email.

Ci vediamo lì! 
"""
            # ✉️ Invia email
            sent = gmail_send_email_template(
                participant_data["email"],
                subject,
                text_content,
                html_content,
                pdf_buffer,
                f"{name_surname}_ticket.pdf"
            )

            if not sent:
                return {"success": False, "error": "Failed to send email"}
            
            update_payload["ticket_sent"] = True
            print(f"✅ Email inviata a {participant_data['email']}")
        else:
            print("⏭️ Email non inviata (send=False)")
        
        # 🔄 Aggiorna Firestore
        db.collection("participants").document(event_id) \
          .collection("participants_event").document(participant_id) \
          .update(update_payload)

        return {"success": True}

    except Exception as e:
        print(f"❌ Errore: {e}")
        log_failed_ticket_email(participant_id, participant_data, str(e))
        return {"success": False, "error": str(e)}


def log_failed_ticket_email(participant_id, participant_data, error_message):
    """Logga l'errore in caso di invio email fallito."""
    try:
        db.collection("contact_message").add({
            "subject": "⚠️ Ticket Email Failed",
            "participant_id": participant_id,
            "event_id": participant_data.get("event_id"),
            "email": participant_data.get("email"),
            "name": participant_data.get("name"),
            "surname": participant_data.get("surname"),
            "error_message": error_message,
            "timestamp":  firestore.SERVER_TIMESTAMP
        })
        print(f"✅ Errore loggato per {participant_id}")
    except Exception as e:
        print(f"❌ Errore logging fallito: {e}")
    
