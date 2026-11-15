from typing import Iterable, List, Optional

from google.cloud import firestore
from google.api_core.exceptions import Aborted, FailedPrecondition

from errors.service_errors import ConflictError, NotFoundError, ValidationError
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from models import Membership
from domain.membership_rules import combine_membership_models
from repositories.membership_integrity import (identity, registrations, validate_registration,
    check_write_limit, operation_record, contact_fences, assert_member_contacts_available, touch_contact_fences,
    assert_no_active_holds, prepare_identity_cascade)
from repositories.base import BaseRepository
from utils.slug_utils import build_slug


class MembershipRepository(BaseRepository[Membership]):
    def __init__(self):
        super().__init__("memberships", Membership)

    def _model_from_snapshot(self, snapshot):
        model = super()._model_from_snapshot(snapshot)
        model._version = snapshot.update_time
        return model

    def get(self, membership_id: str) -> Optional[Membership]:
        if not membership_id:
            return None
        doc = self.collection.document(membership_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def list(self) -> List[Membership]:
        return [self._model_from_snapshot(doc) for doc in self.collection.stream()]

    def get_last_by_start_date(self) -> Optional[Membership]:
        docs = (
            self.collection
            .order_by("start_date", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def get_model_by_slug(self, slug: str) -> Optional[Membership]:
        if not slug:
            return None
        matches = self.collection.where(filter=FieldFilter("slug", "==", slug)).limit(1).get()
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def find_by_email(self, email: str) -> Optional[Membership]:
        if not email:
            return None
        docs = self.collection.where(filter=FieldFilter("email", "==", email)).limit(1).get()
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def find_by_phone(self, phone: str) -> Optional[Membership]:
        if not phone:
            return None
        docs = self.collection.where(filter=FieldFilter("phone", "==", phone)).limit(1).get()
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def create(self, membership: Membership) -> str:
        return self.create_from_model(membership)

    def create_from_model(self, membership: Membership) -> str:
        ref = self.collection.document()
        membership.slug = build_slug(membership.name, membership.surname, suffix=ref.id[-6:])
        data = membership.to_firestore(include_none=True)

        @firestore.transactional
        def create(transaction):
            fences = contact_fences(data, transaction)
            assert_member_contacts_available(data, transaction=transaction)
            touch_contact_fences(transaction, fences)
            transaction.create(ref, data)

        create(db.transaction())
        return ref.id

    def append_purchase(self, membership_id: str, purchase_id: str) -> bool:
        if not membership_id or not purchase_id:
            return False
        self.collection.document(membership_id).update(
            {"purchases": firestore.ArrayUnion([purchase_id])}
        )
        return True

    def add_attended_event_and_purchase(
        self, membership_id: str, event_id: str, purchase_id: str
    ) -> bool:
        if not membership_id or not event_id or not purchase_id:
            return False
        self.collection.document(membership_id).update(
            {
                "attended_events": firestore.ArrayUnion([event_id]),
                "purchases": firestore.ArrayUnion([purchase_id]),
            }
        )
        return True

    def add_attended_event(self, membership_id: str, event_id: str) -> bool:
        if not membership_id or not event_id:
            return False
        self.collection.document(membership_id).update(
            {"attended_events": firestore.ArrayUnion([event_id])}
        )
        return True

    def find_by_year(self, year: int) -> List[Membership]:
        docs = self.collection.where(
            filter=FieldFilter("membership_years", "array_contains", int(year))
        ).stream()
        return [self._model_from_snapshot(doc) for doc in docs]

    def update_from_model(self, membership_id: str, payload: Membership) -> bool:
        ref = self.collection.document(membership_id)
        audit_ref = db.collection('membership_operations').document()

        @firestore.transactional
        def update(transaction):
            current = ref.get(transaction=transaction)
            if not current.exists:
                raise ConflictError('Socio non più presente: ricaricare i dati')
            if getattr(payload, '_version', current.update_time) != current.update_time:
                raise ConflictError('Socio modificato contemporaneamente: ricaricare i dati')
            before = current.to_dict() or {}
            data = payload.to_firestore(include_none=True)
            changed = identity(before) != identity(data)
            fences = contact_fences({**before}, transaction) + contact_fences(data, transaction) if changed else []
            if changed:
                assert_member_contacts_available(data, [membership_id], transaction)
            linked, events = prepare_identity_cascade(membership_id, before, data, transaction)
            check_write_limit(1 + len(linked) + len(events) + len({row.reference.path for row in fences}) + int(changed))
            touch_contact_fences(transaction, fences)
            transaction.update(ref, data)
            for row in linked:
                transaction.update(row.reference, identity(data))
            for event_id in events:
                transaction.update(db.collection('events').document(event_id),
                                   {'capacityRevision': firestore.Increment(1)})
            if changed:
                transaction.create(audit_ref, operation_record('member_identity_updated',
                    source_id=membership_id, target_id=membership_id,
                    before=identity(before), after=identity(data)))
            return len({row.reference.path for row in fences})

        transaction = db.transaction()
        member_write_index = update(transaction)
        payload._version = transaction.write_results[member_write_index].update_time
        return True

    def merge_atomic(self, source_id: str, target_id: str):
        source_ref, target_ref = [self.collection.document(value) for value in (source_id, target_id)]
        audit_ref = db.collection('membership_operations').document()

        @firestore.transactional
        def merge(transaction):
            source_snap = source_ref.get(transaction=transaction)
            target_snap = target_ref.get(transaction=transaction)
            if not source_snap.exists or not target_snap.exists:
                raise NotFoundError('Membership sorgente o destinazione non trovata')
            source = self._model_from_snapshot(source_snap)
            target = self._model_from_snapshot(target_snap)
            # A merge must not silently transfer a Firebase account binding.
            if source.uid and source.uid != target.uid:
                raise ConflictError('Account associato alla sorgente: verifica manuale richiesta')
            merged = combine_membership_models(source, target)
            linked = registrations([source_id, target_id], transaction)
            by_event = {}
            for row in linked:
                event_id = row.reference.parent.parent.id
                if event_id in by_event:
                    raise ConflictError(f'Merge non consentito: due iscrizioni nello stesso evento ({event_id})')
                by_event[event_id] = row
            # Legacy scan documents use the member ID only in the path.
            scans = [row for row in db.collection_group('scans').stream(transaction=transaction)
                     if row.id in (source_id, target_id)]
            scan_events = {}
            for scan in scans:
                event_id = scan.reference.parent.parent.id
                if event_id in scan_events:
                    raise ConflictError(f'Merge non consentito: due ingressi nello stesso evento ({event_id})')
                scan_events[event_id] = scan
            purchases = list(db.collection('purchases').where(filter=FieldFilter(
                'membership_ids', 'array_contains_any', [source_id, target_id])).stream(transaction=transaction))
            discounts = list(db.collection('discount_codes').where(filter=FieldFilter(
                'restrictedMembershipId', '==', source_id)).stream(transaction=transaction))
            assert_no_active_holds([{**source_snap.to_dict(), 'membershipId': source_id},
                                    {**target_snap.to_dict(), 'membershipId': target_id}], transaction)
            for event_id, row in by_event.items():
                data = row.to_dict() or {}
                if (data.get('entered') or data.get('entered_at')) and event_id not in scan_events:
                    raise ConflictError(f'Ingresso storico senza scan: verifica manuale richiesta ({event_id})')
            for event_id, row in by_event.items():
                proposed = {**(row.to_dict() or {}), **identity(merged.to_firestore()), 'membershipId': target_id}
                validate_registration(event_id, proposed, row.id, transaction)
            moves = [scan for scan in scans if scan.id == source_id]
            fences = contact_fences(source_snap.to_dict() or {}, transaction) + contact_fences(
                target_snap.to_dict() or {}, transaction)
            check_write_limit(3 + len(linked) + len(by_event) + len(purchases) + len(discounts)
                              + len({row.reference.path for row in fences}) + 2 * len(moves))
            merged.attended_events = sorted(set(merged.attended_events) | set(by_event) | set(scan_events))
            merged.purchases = sorted(set(merged.purchases) | {row.id for row in purchases})
            touch_contact_fences(transaction, fences)
            for discount in discounts:
                transaction.update(discount.reference, {'restrictedMembershipId': target_id})
            for row in linked:
                event_id = row.reference.parent.parent.id
                scan = scan_events.get(event_id)
                transaction.update(row.reference, {**identity(merged.to_firestore()), 'membershipId': target_id,
                    'membership_included': True, 'entered': scan is not None,
                    'entered_at': (scan.to_dict() or {}).get('scanned_at') if scan else None})
            for scan in moves:
                dest = scan.reference.parent.document(target_id)
                transaction.create(dest, scan.to_dict())
                transaction.delete(scan.reference)
            for purchase in purchases:
                ids = (purchase.to_dict() or {}).get('membership_ids') or []
                transaction.update(purchase.reference, {'membership_ids': sorted(
                    {target_id if value == source_id else value for value in ids})})
            for event_id in by_event:
                transaction.update(db.collection('events').document(event_id),
                                   {'capacityRevision': firestore.Increment(1)})
            transaction.update(target_ref, merged.to_firestore(include_none=True))
            transaction.delete(source_ref)
            transaction.create(audit_ref, operation_record('members_merged', source_id=source_id,
                target_id=target_id, source_snapshot=source_snap.to_dict(),
                target_snapshot=target_snap.to_dict(), events=sorted(set(by_event) | set(scan_events))))
            return {'participants_updated': sum((row.to_dict() or {}).get('membershipId') == source_id
                    for row in linked), 'membership_years': merged.membership_years,
                    'old_wallet_ids': [value for value in (source.wallet_pass_id, target.wallet_pass_id) if value]}

        return merge(db.transaction())

    def delete_unreferenced(self, membership_id: str) -> Membership:
        ref = self.collection.document(membership_id)
        audit_ref = db.collection('membership_operations').document()

        @firestore.transactional
        def delete(transaction):
            snapshot = ref.get(transaction=transaction)
            if not snapshot.exists:
                raise NotFoundError('Membership non trovata')
            data = snapshot.to_dict() or {}
            if data.get('uid') or data.get('purchases') or data.get('purchase_id') or data.get('attended_events'):
                raise ConflictError('Socio con account o storico: eliminazione non consentita')
            if registrations([membership_id], transaction):
                raise ConflictError('Socio collegato a partecipanti: eliminazione non consentita')
            purchases = list(db.collection('purchases').where(filter=FieldFilter(
                'membership_ids', 'array_contains', membership_id)).limit(1).stream(transaction=transaction))
            discounts = list(db.collection('discount_codes').where(filter=FieldFilter(
                'restrictedMembershipId', '==', membership_id)).limit(1).stream(transaction=transaction))
            scans = any(row.id == membership_id for row in db.collection_group('scans').stream(transaction=transaction))
            if purchases or discounts or scans:
                raise ConflictError('Socio con riferimenti o ingressi: eliminazione non consentita')
            assert_no_active_holds([{**data, 'membershipId': membership_id}], transaction)
            fences = contact_fences(data, transaction)
            touch_contact_fences(transaction, fences)
            transaction.delete(ref)
            transaction.create(audit_ref, operation_record('member_deleted', source_id=membership_id,
                target_id=None, source_snapshot=data))
            return self._model_from_snapshot(snapshot)

        return delete(db.transaction())

    def delete(self, membership_id: str) -> None:
        self.delete_unreferenced(membership_id)

    def list_by_purchase_ids(self, purchase_ids: List[str]) -> Iterable[Membership]:
        if not purchase_ids:
            return []
        snaps = (
            self.collection
            .where(filter=FieldFilter("purchase_id", "in", purchase_ids))
            .stream()
        )
        for snap in snaps:
            yield self._model_from_snapshot(snap)

    def clear_wallet(self, membership_id: str) -> None:
        self.collection.document(membership_id).update({
            "wallet_pass_id": None,
            "wallet_url": None,
        })

    def set_wallet(self, membership_id: str, pass_id: str, wallet_url: str) -> None:
        self.collection.document(membership_id).update({
            "wallet_pass_id": pass_id,
            "wallet_url": wallet_url,
        })

    def get_for_account(self, email: str, uid: str, *, allow_link: bool = False,
                        newsletter_consent: Optional[bool] = None) -> Membership:
        """Authorize a unique email/UID binding; commit only the requested fields."""
        denied = "Account not authorized for this membership"
        if not isinstance(email, str) or not email or not isinstance(uid, str) or not uid:
            raise ValidationError(denied)
        if newsletter_consent is not None and type(newsletter_consent) is not bool:
            raise ValidationError("Invalid newsletter consent")
        membership_id = None
        for _ in range(4):
            matches = self.collection.where(filter=FieldFilter("email", "==", email)).limit(2).get()
            if membership_id and (len(matches) != 1 or matches[0].id != membership_id):
                raise ValidationError(denied)
            if not matches and allow_link:
                raise NotFoundError("Membership not found for this account")
            if len(matches) != 1:
                raise ValidationError(denied)
            snapshot = matches[0]
            membership_id = snapshot.id
            data = snapshot.to_dict() or {}
            bound_uid = data.get("uid")
            changes = {}
            if bound_uid in (None, ""):
                if allow_link is not True:
                    raise ValidationError(denied)
                changes["uid"] = uid
            elif bound_uid != uid:
                raise ValidationError(denied)
            if newsletter_consent is not None:
                changes["newsletter_consent"] = newsletter_consent
            if not changes:
                return self._model_from_snapshot(snapshot)
            try:
                snapshot.reference.update(changes,
                    option=firestore.Client.write_option(last_update_time=snapshot.update_time))
            except (Aborted, FailedPrecondition):
                continue
            data.update(changes)
            return Membership.from_firestore(data, snapshot.id)
        raise ConflictError("Membership changed concurrently; retry the request")

    def set_merging(self, membership_id: str, value: Optional[bool]) -> None:
        self.collection.document(membership_id).update({"merging": value})

    def list_by_ids(self, membership_ids: List[str]) -> Iterable[Membership]:
        if not membership_ids:
            return []
        doc_refs = [self.collection.document(member_id) for member_id in membership_ids]
        snaps = (
            self.collection
            .where(filter=FieldFilter("__name__", "in", doc_refs))
            .stream()
        )
        for snap in snaps:
            yield self._model_from_snapshot(snap)
