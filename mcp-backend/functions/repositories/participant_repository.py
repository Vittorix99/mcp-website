from typing import Iterable, List, Optional
from hashlib import sha256
from datetime import datetime, timezone
from domain.registration_rules import assert_registration_available, registration_keys

from google.api_core.exceptions import Aborted, AlreadyExists, FailedPrecondition
from errors.service_errors import ConflictError, NotFoundError

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from models import EventParticipant
from repositories.membership_integrity import (identity, operation_record, contact_fences,
    assert_member_contacts_available, touch_contact_fences, prepare_identity_cascade, check_write_limit)


class ParticipantRepository:
    def __init__(self):
        self.base_collection = db.collection("participants")

    def _chunked(self, values: List[str], size: int = 10) -> Iterable[List[str]]:
        for i in range(0, len(values), size):
            yield values[i:i + size]

    def _collection(self, event_id: str) -> firestore.CollectionReference:
        return self.base_collection.document(event_id).collection("participants_event")

    def _model_from_snapshot(self, snapshot: firestore.DocumentSnapshot, event_id: str) -> EventParticipant:
        model = EventParticipant.from_firestore(snapshot.to_dict() or {}, snapshot.id)
        model._version = snapshot.update_time
        return model

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

    def assert_can_register(self, event_id, email, phone, membership_id=None, participant_id=None):
        self._assert_available(event_id, {'email': email, 'phone': phone, 'membershipId': membership_id}, participant_id)

    @staticmethod
    def _assert_available(event_id, data, participant_id=None, capacity_token=None):
        people = [doc.to_dict() or {} for doc in db.collection('participants').document(event_id)
                  .collection('participants_event').stream() if doc.id != participant_id]
        holds = [(doc.id, doc.to_dict() or {}) for doc in db.collection('event_capacity').document(event_id)
                 .collection('reservations').stream()]
        assert_registration_available(registration_keys(data), people, holds, datetime.now(timezone.utc),
                                      own_token=capacity_token)

    @staticmethod
    def _write(event_id, operation, ref, data=None, capacity_token=None, membership=None, expected_version=None):
        for _ in range(8):
            try:
                return ParticipantRepository._write_once(event_id, operation, ref, data, capacity_token, membership, expected_version)
            except (Aborted, AlreadyExists, FailedPrecondition):
                continue
        raise ConflictError('Iscrizione modificata contemporaneamente: riprova')

    @staticmethod
    def _write_once(event_id, operation, ref, data=None, capacity_token=None, membership=None, expected_version=None):
        event = db.collection('events').document(event_id).get()
        if not event.exists:
            raise NotFoundError('Evento non trovato')
        previous = ref.get() if operation == 'update' else None
        if previous is not None and not previous.exists:
            raise NotFoundError('Partecipante non più presente')
        if previous is not None and expected_version is not None and previous.update_time != expected_version:
            raise ConflictError('Partecipante modificato contemporaneamente: ricaricare i dati')
        original = (previous.to_dict() or {}) if previous is not None else {}
        effective = dict(original)
        if operation == 'update' and original.get('membershipId'):
            locked = {*identity(original), 'membershipId', 'membership_included'}
            if any(key in (data or {}) and data[key] != original.get(key) for key in locked):
                raise ConflictError('Partecipante collegato: modificare dalla scheda socio')
        for key, value in (data or {}).items():
            if value is firestore.DELETE_FIELD:
                effective.pop(key, None)
            else:
                effective[key] = value
        member_ref = member_snapshot = None
        if effective.get('membershipId'):
            member_ref = db.collection('memberships').document(effective['membershipId'])
            member_snapshot = member_ref.get()
            if membership is None and not member_snapshot.exists:
                raise ConflictError('Socio non più presente')
            if membership is not None:
                expected = getattr(membership, '_version', None)
                if (expected is None and member_snapshot.exists) or (expected is not None and
                        (not member_snapshot.exists or member_snapshot.update_time != expected)):
                    raise ConflictError('Socio modificato contemporaneamente')
                member_data = membership.to_firestore(include_none=True)
            else:
                member_data = member_snapshot.to_dict() or {}
            data = {**(data or {}), **identity(member_data), 'membership_included': True}
            effective.update(data)
        fences, cascade_rows, cascade_events = [], [], {}
        if membership is not None and member_snapshot.exists:
            cascade_rows, cascade_events = prepare_identity_cascade(effective['membershipId'],
                member_snapshot.to_dict() or {}, member_data)
        if membership is not None:
            fences = contact_fences(member_data)
            assert_member_contacts_available(member_data, [effective['membershipId']])
        ParticipantRepository._assert_available(event_id, effective, ref.id, capacity_token)
        batch = db.batch()
        touch_contact_fences(batch, fences)
        for row in cascade_rows:
            batch.update(row.reference, identity(member_data),
                         option=db.write_option(last_update_time=row.update_time))
        for cascade_event_id, snapshot in cascade_events.items():
            if cascade_event_id != event_id:
                batch.update(snapshot.reference, {'capacityRevision': firestore.Increment(1)},
                             option=db.write_option(last_update_time=snapshot.update_time))
        check_write_limit(6 + len(fences) + len(cascade_rows) + len(cascade_events))
        batch.update(event.reference, {'capacityRevision': firestore.Increment(1)},
                     option=db.write_option(last_update_time=event.update_time))
        if member_ref is not None:
            fields = {'attended_events': firestore.ArrayUnion([event_id]),
                      'integrityRevision': firestore.Increment(1)}
            if effective.get('purchase_id'):
                fields['purchases'] = firestore.ArrayUnion([effective['purchase_id']])
            if membership is not None:
                fields = {**member_data, **fields}
            if member_snapshot.exists:
                batch.update(member_ref, fields, option=db.write_option(last_update_time=member_snapshot.update_time))
            else:
                batch.create(member_ref, fields)
        if operation == 'update' and not original.get('membershipId') and effective.get('membershipId'):
            if effective.get('entered') or effective.get('entered_at'):
                raise ConflictError('Ingresso già registrato senza tessera: verifica manuale prima del collegamento')
            purchase_id = effective.get('purchase_id')
            if purchase_id:
                purchase_ref = db.collection('purchases').document(purchase_id)
                purchase = purchase_ref.get()
                if not purchase.exists:
                    raise ConflictError('Acquisto non trovato: verifica manuale richiesta')
                batch.update(purchase_ref, {'membership_ids': firestore.ArrayUnion([effective['membershipId']])},
                    option=db.write_option(last_update_time=purchase.update_time))
            batch.create(db.collection('membership_operations').document(), operation_record(
                'participant_linked', source_id=None, target_id=effective['membershipId'],
                event_id=event_id, participant_id=ref.id, before=identity(original)))
        if operation == 'create':
            batch.create(db.collection('membership_operations').document(), operation_record(
                'participant_created', source_id=None, target_id=effective.get('membershipId'),
                event_id=event_id, participant_id=ref.id, membership_created=membership is not None
                    and not member_snapshot.exists, membership_before=(member_snapshot.to_dict()
                        if membership is not None and member_snapshot.exists else None)))
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
            batch.update(ref, data, option=db.write_option(last_update_time=previous.update_time))
        else:
            batch.delete(ref)
        batch.commit()

    def create_from_model(self, event_id: str, participant: EventParticipant, *, membership=None) -> str:
        ref = self._collection(event_id).document()
        self._write(event_id, 'create', ref, participant.to_firestore(include_none=True), membership=membership)
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
        except (AlreadyExists, ConflictError):
            # Another recovery may have completed the hold after our initial lookup.
            snapshot = ref.get()
            if not snapshot.exists:
                raise
            existing = self._model_from_snapshot(snapshot, event_id)
            self.assert_same_checkout(existing, participant)
            return existing.id
        return ref.id

    def update_from_model(self, event_id: str, participant_id: str, participant: EventParticipant) -> bool:
        self._write(event_id, 'update', self._collection(event_id).document(participant_id),
                    participant.to_firestore(include_none=True), expected_version=getattr(participant, '_version', None))
        return True

    def begin_ticket_delivery(self, event_id: str, participant_id: str, *, automatic: bool) -> bool:
        ref = self._collection(event_id).document(participant_id)
        for _ in range(4):
            snapshot = ref.get()
            if not snapshot.exists:
                raise ConflictError('Partecipante non più presente')
            data = snapshot.to_dict() or {}
            if automatic and (data.get('ticket_sent') or data.get('ticket_delivery_started')):
                return False
            try:
                # Sticky before the provider call: an uncertain send requires manual retry.
                ref.update({'ticket_delivery_started': True},
                           option=db.write_option(last_update_time=snapshot.update_time))
                return True
            except (Aborted, FailedPrecondition):
                continue
        raise ConflictError('Invio modificato contemporaneamente: verificare manualmente')

    def update_ticket_delivery(self, event_id: str, participant_id: str, pdf_url: str, sent: bool) -> None:
        fields = {'ticket_pdf_url': pdf_url}
        # Generating a PDF alone must not clear a concurrently confirmed delivery.
        if sent:
            fields['ticket_sent'] = True
        self._collection(event_id).document(participant_id).update(fields)

    def mark_omaggio_email_sent(self, event_id: str, participant_id: str) -> None:
        self._collection(event_id).document(participant_id).update({
            'omaggio_email_sent': True, 'omaggio_email_sent_at': firestore.SERVER_TIMESTAMP,
        })

    def delete(self, event_id: str, participant_id: str) -> None:
        from repositories.event_deletion import delete_without_history

        delete_without_history(event_id, participant_id)

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
        self._write(event_id, 'update', self._collection(event_id).document(participant_id), {
            "membershipId": membership_id or firestore.DELETE_FIELD,
            "membership_included": bool(membership_id),
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

    def sync_entered_by_membership_id(self, event_id: str, membership_id: str) -> None:
        """Mirror the single scan, including when entry and undo overlap."""
        query = self._collection(event_id).where(filter=FieldFilter("membershipId", "==", membership_id))
        references = [doc.reference for doc in query.stream()]
        scan_ref = db.collection("entrance_scans").document(event_id).collection("scans").document(membership_id)

        @firestore.transactional
        def sync(transaction, refs):
            scan = scan_ref.get(transaction=transaction)
            snapshots = list(db.get_all(refs, transaction=transaction))
            fields = {"entered": scan.exists,
                      "entered_at": (scan.to_dict() or {}).get("scanned_at") if scan.exists else None}
            for doc in snapshots:
                data = doc.to_dict() or {}
                if (doc.exists and data.get('membershipId') == membership_id
                        and any(data.get(key) != value for key, value in fields.items())):
                    transaction.update(doc.reference, fields)

        for offset in range(0, len(references), 400):
            sync(db.transaction(), references[offset:offset + 400])

    def update_membership_reference(self, old_membership_id: str, new_membership_id: str) -> int:
        if not old_membership_id or not new_membership_id:
            return 0
        query = db.collection_group("participants_event").where(
            filter=FieldFilter("membershipId", "==", old_membership_id)
        )
        snapshots = list(query.stream())
        events = set()
        for snap in snapshots:
            event_id = snap.reference.parent.parent.id
            if event_id in events or self.get_by_membership_id(event_id, new_membership_id) is not None:
                raise ConflictError('Merge non consentito: socio già iscritto allo stesso evento')
            events.add(event_id)
        updated = 0
        for snap in snapshots:
            event_id = snap.reference.parent.parent.id
            self._write(event_id, 'update', snap.reference, {
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
