from datetime import datetime
from typing import Optional

from google.cloud import firestore

from config.firebase_config import db
from models.scan_token import ScanToken


class ScanTokenRepository:
    def __init__(self):
        self.collection = db.collection("scan_tokens")

    def get(self, token: str) -> Optional[ScanToken]:
        doc = self.collection.document(token).get()
        if not doc.exists:
            return None
        return ScanToken.from_firestore(doc.to_dict() or {}, doc_id=token)

    def create(self, token: str, event_id: str, admin_uid: str, expires_at: datetime) -> None:
        self.collection.document(token).set({
            "event_id": event_id,
            "created_by": admin_uid,
            "created_at": firestore.SERVER_TIMESTAMP,
            "expires_at": expires_at,
            "is_active": True,
        })

    def deactivate(self, token: str, admin_uid: str) -> None:
        self.collection.document(token).update({
            "is_active": False,
            "deactivated_by": admin_uid,
            "deactivated_at": firestore.SERVER_TIMESTAMP,
        })
