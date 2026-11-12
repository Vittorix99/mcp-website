from typing import Iterable, List, Optional
from hashlib import sha256

from google.api_core.exceptions import Aborted, AlreadyExists, FailedPrecondition
from errors.service_errors import ConflictError

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

    @staticmethod
    def _write(event_id, operation, ref, data=None, capacity_token=None):
        batch = db.batch()
        batch.update(db.collection('events').document(event_id), {'capacityRevision': firestore.Increment(1)})
        if capacity_token is not None:
            hold = db.collection('event_capacity').document(event_id).collection('reservations').document(capacity_token).get()
            held = hold.to_dict() or {}
            if (not hold.exists or held.get('state') != 'capturing'
                    or held.get('purchaseId') != data.get('purchase_id')):
                raise ConflictError('Posti già convertiti o non attribuibili: gestione manuale richiesta')
            # A consumed hold may never authorize resurrection after an admin deletion.
            batch.update(hold.reference, {'state': 'capturing'},
                         option=db.write_option(last_update_time=hold.update_time))
        if operation == 'create':
            batch.create(ref, data)
        elif operation == 'update':
            batch.set(ref, data, merge=True)
        else:
            batch.delete(ref)
        batch.commit()

    def create_from_model(self, event_id: str, participant: EventParticipant) -> str:
        ref = self._collection(event_id).document()
        self._write(event_id, 'create', ref, participant.to_firestore(include_none=True))
        return ref.id

    @staticmethod
    def assert_same_checkout(existing: EventParticipant, expected: EventParticipant) -> None:
        if existing.checkout_index is not None and existing.checkout_index != expected.checkout_index:
            raise ConflictError("Participant checkout position is inconsistent")
        fields = ("event_id", "purchase_id", "email", "name", "surname", "phone", "birthdate",
                  "membership_id", "membership_included", "price", "price_original",
                  "discount_code_id", "discount_code", "payment_method")
        if any(getattr(existing, field) != getattr(expected, field) for field in fields):
            raise ConflictError("Participant does not match captured order")

    def create_for_purchase(self, event_id: str, participant: EventParticipant, checkout_index: int = 0,
                           capacity_reservation_id: Optional[str] = None) -> str:
        for _ in range(4):
            try:
                return self._create_for_purchase(event_id, participant, checkout_index, capacity_reservation_id)
            except (Aborted, FailedPrecondition):
                continue
        raise ConflictError('Prenotazione modificata contemporaneamente: riprova il recupero')

    def _create_for_purchase(self, event_id, participant, checkout_index, capacity_reservation_id):
        participant.checkout_index = checkout_index
        collection = self._collection(event_id)
        matches = [doc for doc in collection.where(
            filter=FieldFilter("purchase_id", "==", participant.purchase_id)).stream()
            if (doc.to_dict() or {}).get("email") == participant.email
            and (doc.to_dict() or {}).get("checkoutIndex") in (None, checkout_index)]
        if len(matches) > 1:
            raise ConflictError("Duplicate checkout participants: manual verification required")
        if matches:
            existing = self._model_from_snapshot(matches[0], event_id)
            self.assert_same_checkout(existing, participant)
            return existing.id
        if not isinstance(capacity_reservation_id, str) or not capacity_reservation_id or '/' in capacity_reservation_id:
            raise ConflictError('Nuova partecipazione online senza prenotazione posti')
        key = participant.purchase_id + ":" + str(checkout_index)
        ref = collection.document("checkout-" + sha256(key.encode()).hexdigest())
        try:
            self._write(event_id, 'create', ref, participant.to_firestore(include_none=True), capacity_reservation_id)
        except AlreadyExists:
            existing = self._model_from_snapshot(ref.get(), event_id)
            self.assert_same_checkout(existing, participant)
            return existing.id
        return ref.id

    def update_from_model(self, event_id: str, participant_id: str, participant: EventParticipant) -> bool:
        self._write(event_id, 'update', self._collection(event_id).document(participant_id),
                    participant.to_firestore(include_none=True))
        return True

    def delete(self, event_id: str, participant_id: str) -> None:
        self._write(event_id, 'delete', self._collection(event_id).document(participant_id))

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

    def stream_all(self) -> Iterable[EventParticipant]:
        for snap in db.collection_group("participants_event").stream():
            payload = snap.to_dict() or {}
            event_ref = snap.reference.parent.parent
            event_id = event_ref.id if event_ref else payload.get("event_id", "")
            if event_id:
                payload["event_id"] = payload.get("event_id") or event_id
            yield EventParticipant.from_firestore(payload, snap.id)
