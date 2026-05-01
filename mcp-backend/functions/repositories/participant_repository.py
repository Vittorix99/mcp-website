from typing import Iterable, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
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

    def list(self, event_id: str) -> List[EventParticipant]:
        docs = self._collection(event_id).stream()
        return [self._model_from_snapshot(doc, event_id) for doc in docs]

    def stream(self, event_id: str) -> Iterable[EventParticipant]:
        for doc in self._collection(event_id).stream():
            yield self._model_from_snapshot(doc, event_id)

    def get(self, event_id: str, participant_id: str) -> Optional[EventParticipant]:
        doc = self._collection(event_id).document(participant_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc, event_id)

    def create_from_model(self, event_id: str, participant: EventParticipant) -> str:
        doc_ref = self._collection(event_id).add(participant.to_firestore(include_none=True))[1]
        return doc_ref.id

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

    def get_last_across_events(self) -> Optional[EventParticipant]:
        docs = (
            db.collection_group("participants_event")
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        return EventParticipant.from_firestore(docs[0].to_dict() or {}, docs[0].id)

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
            snap.reference.update({
                "membershipId": firestore.DELETE_FIELD,
                "membership_included": False,
            })
            updated += 1
        return updated

    def get_by_membership_id(self, event_id: str, membership_id: str) -> Optional["EventParticipant"]:
        """Return the first participant in the given event whose membershipId matches."""
        docs = (
            db.collection_group("participants_event")
            .where(filter=FieldFilter("membershipId", "==", membership_id))
            .get()
        )
        for doc in docs:
            if doc.reference.parent.parent.id == event_id:
                return EventParticipant.from_firestore(doc.to_dict() or {}, doc.id)
        return None

    def update_entered(self, event_id: str, participant_id: str, entered: bool) -> None:
        self._collection(event_id).document(participant_id).update({
            "entered": entered,
            "entered_at": firestore.SERVER_TIMESTAMP if entered else None,
        })

    def update_membership_reference(self, old_membership_id: str, new_membership_id: str) -> int:
        if not old_membership_id or not new_membership_id:
            return 0
        query = db.collection_group("participants_event").where(
            filter=FieldFilter("membershipId", "==", old_membership_id)
        )
        updated = 0
        for snap in query.stream():
            snap.reference.update({
                "membershipId": new_membership_id,
                "membership_included": True,
            })
            updated += 1
        return updated
