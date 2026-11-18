from typing import Optional

from google.cloud import firestore

from models.scan_token import ScanToken
from errors.service_errors import NotFoundError
from config.firebase_config import db
from repositories.base import BaseRepository


class ScanTokenRepository(BaseRepository[ScanToken]):
    def __init__(self):
        super().__init__("scan_tokens", ScanToken)

    def get(self, token: str) -> Optional[ScanToken]:
        doc = self.collection.document(token).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def create(self, token: str, event_id: str, admin_uid: str, expires_at) -> None:
        model = ScanToken(
            event_id=event_id,
            created_by=admin_uid,
            created_at=firestore.SERVER_TIMESTAMP,
            expires_at=expires_at,
            is_active=True,
        )
        @firestore.transactional
        def create(transaction):
            event = db.collection("events").document(event_id).get(transaction=transaction)
            if not event.exists:
                raise NotFoundError("Evento non più presente")
            transaction.create(self.collection.document(token), model.to_firestore())

        create(db.transaction())

    def deactivate(self, token: str, admin_uid: str) -> None:
        self.collection.document(token).update({
            "is_active": False,
            "deactivated_by": admin_uid,
            "deactivated_at": firestore.SERVER_TIMESTAMP,
        })
