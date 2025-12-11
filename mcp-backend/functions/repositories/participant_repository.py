from typing import Dict, Iterable, List, Optional, Union

from google.cloud import firestore

from config.firebase_config import db
from dto import EventParticipantDTO
from models import EventParticipant


class ParticipantRepository:
    def __init__(self):
        self.base_collection = db.collection("participants")

    def _collection(self, event_id: str) -> firestore.CollectionReference:
        return self.base_collection.document(event_id).collection("participants_event")

    def _model_from_snapshot(self, snapshot: firestore.DocumentSnapshot, event_id: str) -> EventParticipant:
        return EventParticipant.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def _dto_from_snapshot(self, snapshot: firestore.DocumentSnapshot, event_id: str) -> EventParticipantDTO:
        model = self._model_from_snapshot(snapshot, event_id)
        return EventParticipantDTO.from_model(model)

    def list(self, event_id: str) -> List[EventParticipantDTO]:
        docs = self._collection(event_id).stream()
        return [self._dto_from_snapshot(doc, event_id) for doc in docs]

    def stream(self, event_id: str) -> Iterable[EventParticipantDTO]:
        for doc in self._collection(event_id).stream():
            yield self._dto_from_snapshot(doc, event_id)

    def get(self, event_id: str, participant_id: str) -> Optional[EventParticipantDTO]:
        doc = self._collection(event_id).document(participant_id).get()
        if not doc.exists:
            return None
        return self._dto_from_snapshot(doc, event_id)

    def create(self, event_id: str, payload: Union[Dict[str, Optional[str]], EventParticipantDTO]) -> str:
        if hasattr(payload, "to_payload"):
            data = payload.to_payload()
        else:
            data = payload
        doc_ref = self._collection(event_id).add(data)[1]
        return doc_ref.id

    def update(self, event_id: str, participant_id: str, payload: Union[Dict[str, Optional[str]], EventParticipantDTO]) -> bool:
        if hasattr(payload, "to_payload"):
            data = payload.to_payload()
        else:
            data = payload
        self._collection(event_id).document(participant_id).set(data, merge=True)
        return True

    def delete(self, event_id: str, participant_id: str) -> None:
        self._collection(event_id).document(participant_id).delete()
