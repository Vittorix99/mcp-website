from typing import List, Optional

from google.cloud import firestore

from models import ContactMessage
from repositories.base import BaseRepository


class MessageRepository(BaseRepository[ContactMessage]):
    def __init__(self):
        super().__init__("contact_message", ContactMessage)

    def list_models_ordered_by_name(self) -> List[ContactMessage]:
        docs = self.collection.order_by("name").stream()
        return [self._model_from_snapshot(doc) for doc in docs]

    def count_unanswered_since(self, time_limit) -> int:
        query = (
            self.collection
            .where("answered", "==", False)
            .where("timestamp", ">=", time_limit)
            .stream()
        )
        return sum(1 for _ in query)

    def get_last_model(self) -> Optional[ContactMessage]:
        docs = (
            self.collection
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def get_model(self, message_id: str) -> Optional[ContactMessage]:
        return self.get_by_id(message_id)

    def create_from_model(self, payload: ContactMessage) -> str:
        return self.collection.add(payload.to_firestore(include_none=True))[1].id

    def delete(self, message_id: str) -> None:
        self.collection.document(message_id).delete()

    def update_from_model(self, message_id: str, payload: ContactMessage) -> None:
        self.collection.document(message_id).set(payload.to_firestore(include_none=True), merge=True)
