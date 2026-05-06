from typing import Optional

from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore

from config.firebase_config import db
from models import EntranceScan


class EntranceScanRepository:
    """Repository su subcollection: il path dipende dall'evento, quindi non usa BaseRepository."""

    def __init__(self):
        self.base_collection = db.collection("entrance_scans")

    def _collection(self, event_id: str):
        return self.base_collection.document(event_id).collection("scans")

    def _model_from_snapshot(self, snapshot) -> EntranceScan:
        return EntranceScan.from_firestore(snapshot.to_dict() or {}, doc_id=snapshot.id)

    def get(self, event_id: str, membership_id: str) -> Optional[EntranceScan]:
        doc = self._collection(event_id).document(membership_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def exists(self, event_id: str, membership_id: str) -> bool:
        return self._collection(event_id).document(membership_id).get().exists

    def list(self, event_id: str):
        return [self._model_from_snapshot(doc) for doc in self._collection(event_id).stream()]

    def create_scan(self, event_id: str, membership_id: str, scan_token: str) -> Optional[EntranceScan]:
        """Ritorna None se crea il record; ritorna lo scan esistente se intercetta una race condition."""
        model = EntranceScan(
            scanned_at=firestore.SERVER_TIMESTAMP,
            scan_token=scan_token,
            manual=False,
        )
        ref = self._collection(event_id).document(membership_id)
        try:
            ref.create(model.to_firestore())
            return None
        except AlreadyExists:
            return self._model_from_snapshot(ref.get())

    def create_manual(self, event_id: str, membership_id: str, admin_uid: str) -> None:
        model = EntranceScan(
            scanned_at=firestore.SERVER_TIMESTAMP,
            manual=True,
            operator=admin_uid,
        )
        self._collection(event_id).document(membership_id).set(model.to_firestore())

    def delete(self, event_id: str, membership_id: str) -> None:
        self._collection(event_id).document(membership_id).delete()

    def count(self, event_id: str) -> int:
        return sum(1 for _ in self._collection(event_id).stream())
