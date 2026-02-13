from typing import Dict, Iterable, List, Optional, Union

from google.cloud import firestore

from config.firebase_config import db
from dto import ContactMessageDTO
from models import ContactMessage


class MessageRepository:
    def __init__(self):
        self.collection = db.collection("contact_message")

    def _model_from_snapshot(self, snapshot: firestore.DocumentSnapshot) -> ContactMessage:
        return ContactMessage.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def _dto_from_snapshot(self, snapshot: firestore.DocumentSnapshot) -> ContactMessageDTO:
        model = self._model_from_snapshot(snapshot)
        return ContactMessageDTO.from_model(model)

    def list(self) -> List[ContactMessageDTO]:
        return [self._dto_from_snapshot(doc) for doc in self.collection.stream()]

    def list_ordered_by_name(self) -> List[ContactMessageDTO]:
        docs = self.collection.order_by("name").stream()
        return [self._dto_from_snapshot(doc) for doc in docs]

    def count_unanswered_since(self, time_limit) -> int:
        query = (
            self.collection
            .where("answered", "==", False)
            .where("timestamp", ">=", time_limit)
            .stream()
        )
        return sum(1 for _ in query)

    def get_last_dto(self) -> Optional[ContactMessageDTO]:
        docs = (
            self.collection
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        return self._dto_from_snapshot(docs[0])

    def stream(self) -> Iterable[ContactMessageDTO]:
        for doc in self.collection.stream():
            yield self._dto_from_snapshot(doc)

    def get(self, message_id: str) -> Optional[ContactMessageDTO]:
        doc = self.collection.document(message_id).get()
        if not doc.exists:
            return None
        return self._dto_from_snapshot(doc)

    def create(self, payload: Union[Dict[str, Optional[str]], ContactMessageDTO]) -> str:
        if hasattr(payload, "to_payload"):
            data = payload.to_payload()
        else:
            data = payload
        return self.collection.add(data)[1].id

    def create_from_model(self, payload: ContactMessage) -> str:
        return self.collection.add(payload.to_firestore(include_none=True))[1].id

    def delete(self, message_id: str) -> None:
        self.collection.document(message_id).delete()

    def update(self, message_id: str, payload: Union[Dict[str, Optional[str]], ContactMessageDTO, ContactMessage]) -> None:
        if hasattr(payload, "to_payload"):
            data = payload.to_payload()
        elif hasattr(payload, "to_firestore"):
            data = payload.to_firestore(include_none=True)
        else:
            data = payload
        self.collection.document(message_id).set(data, merge=True)
