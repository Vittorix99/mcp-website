from typing import Dict, Any
from config.firebase_config import db
from services.mail_service import gmail_send_email
from flask import jsonify
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('MessagesService')

class MessagesService:
    def __init__(self):
        self.db = db
        self.collection_name = 'contact_message'
        self.logger = logger

    def get_all(self):
        try:
            self.logger.debug("Fetching all contact messages from Firestore.")
            messages = self.db.collection(self.collection_name).order_by("name").stream()
            result = [
                {
                    "id": doc.id,
                    **doc.to_dict()
                } for doc in messages
            ]
            self.logger.debug(f"Found {len(result)} messages.")
            return jsonify(result), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {'error': str(e)}, 500

    def delete_by_id(self, message_id: str):
        try:
            self.logger.debug(f"Deleting contact message with ID: {message_id}")
            if not message_id:
                return {'error': 'Message ID is required'}, 400

            self.db.collection(self.collection_name).document(message_id).delete()
            return jsonify({"success": True, "deletedId": message_id}), 200
        except Exception as e:
            self.logger.error(f"[delete_by_id] {e}")
            return {'error': str(e)}, 500

    def reply(self, to: str, subject: str, body: str, message_id: str):
        try:
            self.logger.debug(f"Sending email reply to: {to}, subject: {subject}")

            if not to or not body or not message_id:
                return {'error': 'Missing required fields'}, 400

            # ✉️ Send the email
            gmail_send_email(
                to_email=to,
                subject=subject or "Risposta al tuo messaggio",
                body= body
            )

            # ✅ Mark the message as answered in Firestore
            self.db.collection(self.collection_name).document(message_id).update({
                "answered": True
            })

            self.logger.info(f"Marked message {message_id} as answered")
            return jsonify({"success": True, "emailSentTo": to}), 200
        except Exception as e:
            self.logger.error(f"[reply] {e}")
            return {'error': str(e)}, 500