from typing import Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from errors.service_errors import NotFoundError

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

    def _create(self, event_id: str, membership_id: str, model: EntranceScan) -> Optional[EntranceScan]:
        ref = self._collection(event_id).document(membership_id)

        @firestore.transactional
        def create(transaction):
            # Revalidate registration at write time so deletion cannot leave an orphan scan.
            event = db.collection("events").document(event_id).get(transaction=transaction)
            participants = db.collection("participants").document(event_id).collection("participants_event")
            registered = list(participants.where(filter=FieldFilter("membershipId", "==", membership_id))
                              .limit(1).stream(transaction=transaction))
            if not event.exists or not registered:
                raise NotFoundError("Partecipante o evento non più presente")
            existing = ref.get(transaction=transaction)
            if existing.exists:
                return self._model_from_snapshot(existing)
            transaction.create(ref, model.to_firestore())
            return None

        return create(db.transaction())

    def create_scan(self, event_id: str, membership_id: str, scan_token: str) -> Optional[EntranceScan]:
        """Create once for both scanners; return the existing scan on a retry/race."""
        return self._create(event_id, membership_id, EntranceScan(
            scanned_at=firestore.SERVER_TIMESTAMP, scan_token=scan_token, manual=False,
        ))

    def create_manual(self, event_id: str, membership_id: str, admin_uid: str) -> Optional[EntranceScan]:
        return self._create(event_id, membership_id, EntranceScan(
            scanned_at=firestore.SERVER_TIMESTAMP, manual=True, operator=admin_uid,
        ))

    def delete(self, event_id: str, membership_id: str) -> None:
        self._collection(event_id).document(membership_id).delete()

    def count(self, event_id: str) -> int:
        return sum(1 for _ in self._collection(event_id).stream())
