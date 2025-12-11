import logging
import os
from typing import Any, Dict, List

from firebase_admin import firestore

from config.firebase_config import db
from models import NewsletterSignup
from services.mail_service import gmail_send_email_template
from utils.email_templates import get_newsletter_signup_template, get_newsletter_signup_text

logger = logging.getLogger("NewsletterService")


class NewsletterService:
    def __init__(self):
        self.db = db
        self.collection = db.collection("newsletter_signups")
        self.participants_collection = db.collection("newsletter_participants")
        self.logger = logger

    def _serialize(self, signup: NewsletterSignup) -> Dict[str, Any]:
        payload = signup.to_firestore(include_none=True)
        payload["id"] = signup.id
        return payload

    def signup(self, data: Dict[str, Any]) -> tuple:
        self.logger.debug("Starting newsletter signup process")
        email = data.get("email")
        if not email:
            return {"error": "Missing required fields"}, 400

        try:
            existing = self.collection.where("email", "==", email).limit(1).get()
            if not existing:
                signup = NewsletterSignup(email=email, timestamp=firestore.SERVER_TIMESTAMP)
                self.collection.add(signup.to_firestore(include_none=True))

            logo_url = "https://musiconnectingpeople.com/logonew.png"
            instagram_url = os.environ.get("INSTAGRAM_URL")
            html = get_newsletter_signup_template(email, logo_url, instagram_url)
            text = get_newsletter_signup_text(email)

            subject = "Welcome to MCP Newsletter!"

            gmail_send_email_template(email, subject, text, html)
            self.logger.info("Newsletter email sent to %s", email)

            return {"message": "Signed up for newsletter successfully"}, 200

        except Exception as e:
            self.logger.error(f"Error during signup: {e}")
            return {"error": str(e)}, 500

    def get_by_id(self, signup_id: str) -> tuple:
        try:
            doc = self.collection.document(signup_id).get()
            if not doc.exists:
                return {"error": "Newsletter signup not found"}, 404

            signup = NewsletterSignup.from_firestore(doc.to_dict() or {}, doc.id)
            return {"signup": self._serialize(signup)}, 200
        except Exception as e:
            self.logger.error(f"Error getting signup by ID: {e}")
            return {"error": "Internal error occurred"}, 500

    def get_all(self) -> tuple:
        try:
            docs = self.collection.order_by("timestamp", direction=firestore.Query.DESCENDING).get()
            signups = [self._serialize(NewsletterSignup.from_firestore(doc.to_dict() or {}, doc.id)) for doc in docs]
            return {"signups": signups}, 200
        except Exception as e:
            self.logger.error(f"Error getting all signups: {e}")
            return {"error": "Internal error occurred"}, 500

    def update(self, signup_id: str, data: Dict[str, Any]) -> tuple:
        try:
            doc_ref = self.collection.document(signup_id)
            doc = doc_ref.get()
            if not doc.exists:
                return {"error": "Newsletter signup not found"}, 404

            signup = NewsletterSignup.from_firestore(doc.to_dict() or {}, doc.id)
            if "active" in data:
                signup.active = bool(data["active"])
                doc_ref.set(signup.to_firestore(include_none=True))
                return {"message": "Newsletter signup updated successfully"}, 200
            else:
                return {"error": "No valid fields to update"}, 400
        except Exception as e:
            self.logger.error(f"Error updating signup: {e}")
            return {"error": "Internal error occurred"}, 500

    def delete(self, signup_id: str) -> tuple:
        try:
            doc_ref = self.collection.document(signup_id)
            if not doc_ref.get().exists:
                return {"error": "Newsletter signup not found"}, 404

            doc_ref.delete()
            return {"message": "Newsletter signup deleted successfully"}, 200
        except Exception as e:
            self.logger.error(f"Error deleting signup: {e}")
            return {"error": "Internal error occurred"}, 500

    def add_participants(self, participants: List[Dict[str, Any]]) -> tuple:
        self.logger.debug("Adding participants to newsletter_participants")
        if not isinstance(participants, list) or len(participants) == 0:
            return {"error": "Invalid or empty participants array"}, 400

        try:
            batch = self.db.batch()
            for p in participants:
                email = p.get("email")
                if not email or "@" not in email:
                    continue

                doc_ref = self.participants_collection.document()
                batch.set(doc_ref, {**p, "timestamp": firestore.SERVER_TIMESTAMP})

            batch.commit()
            self.logger.info("Added %s participants to newsletter_participants", len(participants))
            return {"message": "Participants added successfully"}, 200
        except Exception as e:
            self.logger.error(f"Error adding participants: {e}")
            return {"error": str(e)}, 500
