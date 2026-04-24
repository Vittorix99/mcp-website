from typing import Optional

from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore

from config.firebase_config import db


class EntranceScanRepository:
    def __init__(self):
        self.base_collection = db.collection("entrance_scans")

    def _collection(self, event_id: str):
        return self.base_collection.document(event_id).collection("scans")

    def get(self, event_id: str, membership_id: str) -> Optional[dict]:
        doc = self._collection(event_id).document(membership_id).get()
        if not doc.exists:
            return None
        return doc.to_dict() or {}

    def exists(self, event_id: str, membership_id: str) -> bool:
        return self._collection(event_id).document(membership_id).get().exists

    def create_scan(self, event_id: str, membership_id: str, scan_token: str) -> Optional[dict]:
        """Returns None if newly created; existing doc data dict if already exists (race condition)."""
        ref = self._collection(event_id).document(membership_id)
        try:
            ref.create({"scanned_at": firestore.SERVER_TIMESTAMP, "scan_token": scan_token})
            return None
        except AlreadyExists:
            return ref.get().to_dict() or {}

    def create_manual(self, event_id: str, membership_id: str, admin_uid: str) -> None:
        self._collection(event_id).document(membership_id).set({
            "scanned_at": firestore.SERVER_TIMESTAMP,
            "manual": True,
            "operator": admin_uid,
        })

    def delete(self, event_id: str, membership_id: str) -> None:
        self._collection(event_id).document(membership_id).delete()

    def count(self, event_id: str) -> int:
        return sum(1 for _ in self._collection(event_id).stream())
