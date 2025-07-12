from typing import Optional, Dict, Any, List
from config.firebase_config import db
from firebase_admin import firestore
from services.mail_service import gmail_send_email_template
from utils.email_templates import get_newsletter_signup_template, get_newsletter_signup_text
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('NewsletterService')


class NewsletterService:
    def __init__(self):
        self.db = db
        self.collection = db.collection("newsletter_signups")
        self.participants_collection = db.collection("newsletter_participants")
        self.logger = logger

    def signup(self, data: Dict[str, Any]) -> tuple:
        self.logger.debug("Starting newsletter signup process")
        email = data.get("email")
        if not email:
            return {"error": "Missing required fields"}, 400

        try:
            existing = self.collection.where("email", "==", email).limit(1).get()
            if not existing:
                self.collection.add({
                    "email": email,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

            # Prepara contenuto email
            logo_url = "https://musiconnectingpeople.com/logonew.png"
            instagram_url = os.environ.get("INSTAGRAM_URL")
            html = get_newsletter_signup_template(email, logo_url, instagram_url)
            text = get_newsletter_signup_text(email)

            subject = "Welcome to MCP Newsletter!"

            gmail_send_email_template(email, subject, text, html)
            self.logger.info(f"Newsletter email sent to {email}")

            return {"message": "Signed up for newsletter successfully"}, 200

        except Exception as e:
            self.logger.error(f"Error during signup: {e}")
            return {"error": str(e)}, 500

    def get_by_id(self, signup_id: str) -> tuple:
        try:
            doc = self.collection.document(signup_id).get()
            if not doc.exists:
                return {"error": "Newsletter signup not found"}, 404

            data = doc.to_dict()
            data["id"] = doc.id
            return {"signup": data}, 200
        except Exception as e:
            self.logger.error(f"Error getting signup by ID: {e}")
            return {"error": "Internal error occurred"}, 500

    def get_all(self) -> tuple:
        try:
            docs = self.collection.order_by("timestamp", direction=firestore.Query.DESCENDING).get()
            signups = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                signups.append(data)
            return {"signups": signups}, 200
        except Exception as e:
            self.logger.error(f"Error getting all signups: {e}")
            return {"error": "Internal error occurred"}, 500

    def update(self, signup_id: str, data: Dict[str, Any]) -> tuple:
        try:
            doc_ref = self.collection.document(signup_id)
            if not doc_ref.get().exists:
                return {"error": "Newsletter signup not found"}, 404

            if "active" in data:
                doc_ref.update({"active": data["active"]})
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
                    continue  # skip invalid email

                doc_ref = self.participants_collection.document()
                batch.set(doc_ref, {
                    **p,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

            batch.commit()
            self.logger.info(f"Added {len(participants)} participants to newsletter_participants")
            return {"message": "Participants added successfully"}, 200
        except Exception as e:
            self.logger.error(f"Error adding participants: {e}")
            return {"error": str(e)}, 500