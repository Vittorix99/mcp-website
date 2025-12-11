import logging
import os
from typing import Any, Dict

from flask import jsonify
from google.cloud import firestore

from config.firebase_config import db
from models import ContactMessage
from services.mail_service import gmail_send_email

logger = logging.getLogger("MessagesService")


class MessagesService:
    def __init__(self):
        self.db = db
        self.collection = self.db.collection("contact_message")
        self.logger = logger

    def _serialize(self, message: ContactMessage) -> Dict[str, Any]:
        payload = message.to_firestore(include_none=True)
        payload["id"] = message.id
        return payload

    def get_all(self):
        try:
            self.logger.debug("Fetching all contact messages from Firestore.")
            messages = self.collection.order_by("name").stream()
            result = [self._serialize(ContactMessage.from_firestore(doc.to_dict() or {}, doc.id)) for doc in messages]
            self.logger.debug("Found %s messages.", len(result))
            return jsonify(result), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {"error": str(e)}, 500

    def delete_by_id(self, message_id: str):
        try:
            self.logger.debug("Deleting contact message with ID: %s", message_id)
            if not message_id:
                return {"error": "Message ID is required"}, 400

            self.collection.document(message_id).delete()
            return jsonify({"success": True, "deletedId": message_id}), 200
        except Exception as e:
            self.logger.error(f"[delete_by_id] {e}")
            return {"error": str(e)}, 500

    def reply(self, to: str, subject: str, body: str, message_id: str):
        try:
            self.logger.debug("Sending email reply to: %s, subject: %s", to, subject)

            if not to or not body or not message_id:
                return {"error": "Missing required fields"}, 400

            gmail_send_email(
                to_email=to,
                subject=subject or "Risposta al tuo messaggio",
                body=body,
            )

            self.collection.document(message_id).update({"answered": True})
            self.logger.info("Marked message %s as answered", message_id)
            return jsonify({"success": True, "emailSentTo": to}), 200
        except Exception as e:
            self.logger.error(f"[reply] {e}")
            return {"error": str(e)}, 500

    def submit_contact_message(self, data: Dict[str, Any]):
        try:
            required = {"name", "email", "message"}
            if not required.issubset(data.keys()):
                return {"error": "Missing required fields"}, 400

            name = data["name"]
            email = data["email"]
            message_text = data["message"]
            send_copy = data.get("send_copy")

            to_email = os.environ.get("USER_EMAIL")
            subject = f"Contact Us Form Submission from {name}"
            body = f"Name: {name}\nEmail: {email}\n\n{message_text}"

            sent = gmail_send_email(to_email, subject, body)
            if not sent:
                return {"error": "Failed to send message"}, 500

            message = ContactMessage(
                name=name,
                email=email,
                message=message_text,
                answered=False,
                timestamp=firestore.SERVER_TIMESTAMP,
            )
            doc_ref = self.collection.add(message.to_firestore(include_none=True))[1]
            self.logger.info("Contact message stored with id %s", doc_ref.id)

            if send_copy:
                gmail_send_email(
                    to_email=email,
                    subject="Copia del tuo messaggio",
                    body=body,
                )
            return {"message": "Message sent successfully"}, 200
        except Exception as e:
            self.logger.error(f"[submit_contact_message] {e}")
            return {"error": f"ERROR IN SENDING MAIL: {str(e)}"}, 500
