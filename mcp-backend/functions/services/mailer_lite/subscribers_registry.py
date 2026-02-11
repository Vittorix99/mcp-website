import logging
from typing import Optional

from firebase_admin import firestore

from config.firebase_config import db
from utils.events_utils import normalize_email

logger = logging.getLogger("MailerLiteSubscribersRegistry")


class MailerLiteSubscribersRegistry:
    def __init__(self):
        self.collection = db.collection("subscribers_mailerlite")

    def get(self, email: str) -> Optional[dict]:
        normalized = normalize_email(email)
        if not normalized:
            return None
        snap = self.collection.document(normalized).get()
        if not snap.exists:
            return None
        return snap.to_dict() or {}

    def upsert(self, email: str, mailerlite_id: Optional[str]) -> None:
        normalized = normalize_email(email)
        if not normalized:
            raise ValueError("Email is required to store subscriber")

        payload = {
            "email": normalized,
            "mailerlite_id": str(mailerlite_id) if mailerlite_id else None,
            "synced_at": firestore.SERVER_TIMESTAMP,
        }

        self.collection.document(normalized).set(payload, merge=True)
