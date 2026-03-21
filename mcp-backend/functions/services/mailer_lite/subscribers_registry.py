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

    def delete_by_email(self, email: str) -> bool:
        normalized = normalize_email(email)
        if not normalized:
            return False
        self.collection.document(normalized).delete()
        return True

    def delete_by_mailerlite_id(self, mailerlite_id: Optional[str]) -> int:
        if not mailerlite_id:
            return 0
        target = str(mailerlite_id)
        deleted = 0
        for snap in self.collection.where("mailerlite_id", "==", target).stream():
            snap.reference.delete()
            deleted += 1
        return deleted
