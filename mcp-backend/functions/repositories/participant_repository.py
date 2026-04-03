from typing import Dict, Iterable, List, Optional, Union

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from dto import EventParticipantDTO
from models import EventParticipant


class ParticipantRepository:
    def __init__(self):
        self.base_collection = db.collection("participants")

    def _chunked(self, values: List[str], size: int = 10) -> Iterable[List[str]]:
        for i in range(0, len(values), size):
            yield values[i:i + size]

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

    def create_from_model(self, event_id: str, participant: EventParticipant) -> str:
        doc_ref = self._collection(event_id).add(participant.to_firestore(include_none=True))[1]
        return doc_ref.id

    def update(self, event_id: str, participant_id: str, payload: Union[Dict[str, Optional[str]], EventParticipantDTO]) -> bool:
        if hasattr(payload, "to_update_payload"):
            data = payload.to_update_payload()  # type: ignore[attr-defined]
        elif hasattr(payload, "to_payload"):
            data = payload.to_payload()
        else:
            data = payload
        self._collection(event_id).document(participant_id).set(data, merge=True)
        return True

    def update_from_model(self, event_id: str, participant_id: str, participant: EventParticipant) -> bool:
        self._collection(event_id).document(participant_id).set(
            participant.to_firestore(include_none=True),
            merge=True,
        )
        return True

    def delete(self, event_id: str, participant_id: str) -> None:
        self._collection(event_id).document(participant_id).delete()

    def count(self, event_id: str) -> int:
        try:
            return sum(1 for _ in self._collection(event_id).stream())
        except Exception:
            return 0

    def any_with_contacts(self, event_id: str, emails: List[str], phones: List[str]) -> bool:
        if not event_id:
            return False
        collection = self._collection(event_id)
        if emails:
            for batch in self._chunked(list(emails)):
                q = collection.where(filter=FieldFilter("email", "in", batch)).limit(1)
                if any(True for _ in q.stream()):
                    return True
        if phones:
            for batch in self._chunked(list(phones)):
                q = collection.where(filter=FieldFilter("phone", "in", batch)).limit(1)
                if any(True for _ in q.stream()):
                    return True
        return False

    def get_last_across_events(self) -> Optional[EventParticipantDTO]:
        docs = (
            db.collection_group("participants_event")
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        model = EventParticipant.from_firestore(docs[0].to_dict() or {}, docs[0].id)
        return EventParticipantDTO.from_model(model)

    def set_membership(self, event_id: str, participant_id: str, membership_id: Optional[str]) -> None:
        """Set or clear the membershipId field on a participant document."""
        if membership_id:
            self._collection(event_id).document(participant_id).update({
                "membershipId": membership_id,
                "membership_included": True,
            })
        else:
            self._collection(event_id).document(participant_id).update({
                "membershipId": firestore.DELETE_FIELD,
                "membership_included": False,
            })

    def clear_membership_reference(self, membership_id: str) -> int:
        if not membership_id:
            return 0
        query = db.collection_group("participants_event").where(
            filter=FieldFilter("membershipId", "==", membership_id)
        )
        updated = 0
        for snap in query.stream():
            snap.reference.update({"membershipId": firestore.DELETE_FIELD})
            updated += 1
        return updated
