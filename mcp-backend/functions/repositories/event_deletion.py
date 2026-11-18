"""Transactional deletion of registrations/events without receipt or entrance history."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from errors.service_errors import ConflictError, NotFoundError


def _assert_free(snapshot):
    data = snapshot.to_dict() or {}
    # Deletion is stricter than revenue eligibility: uncertain money needs review.
    try:
        amount = Decimal(str(data['price'])) if data.get('price') is not None else Decimal(0)
        has_money = not amount.is_finite() or amount != 0
    except (InvalidOperation, ValueError, TypeError):
        has_money = True
    if data.get('purchase_id') or data.get('entered') or data.get('entered_at') or has_money:
        raise ConflictError('Cancellazione non consentita: storico economico o ingressi da conservare')


def delete_without_history(event_id, participant_id=None):
    event_ref = db.collection('events').document(event_id)
    people = db.collection('participants').document(event_id).collection('participants_event')
    scans = db.collection('entrance_scans').document(event_id).collection('scans')

    @firestore.transactional
    def remove(transaction):
        event = event_ref.get(transaction=transaction)
        if not event.exists:
            raise NotFoundError('Evento non trovato')
        registrations = list(people.stream(transaction=transaction))
        selected = [doc for doc in registrations if participant_id is None or doc.id == participant_id]
        if participant_id is not None and not selected:
            raise NotFoundError('Partecipante non trovato')
        for doc in selected:
            _assert_free(doc)
        deletes = [doc.reference for doc in selected]
        membership_updates = []
        if participant_id is not None:
            membership_id = (selected[0].to_dict() or {}).get('membershipId')
            if membership_id:
                scan = scans.document(membership_id).get(transaction=transaction)
                if scan.exists:
                    raise ConflictError('Cancellazione non consentita: ingresso registrato per il socio')
                purchases = db.collection('purchases').where(
                    filter=FieldFilter('membership_ids', 'array_contains', membership_id))
                if any((doc.to_dict() or {}).get('ref_id') == event_id
                       or (doc.to_dict() or {}).get('event_id') == event_id
                       for doc in purchases.stream(transaction=transaction)):
                    raise ConflictError('Cancellazione non consentita: acquisti collegati al socio')
                if not any(doc.id != participant_id and (doc.to_dict() or {}).get('membershipId') == membership_id
                           for doc in registrations):
                    member = db.collection('memberships').document(membership_id).get(transaction=transaction)
                    if member.exists:
                        membership_updates.append(member.reference)
        else:
            if list(scans.limit(1).stream(transaction=transaction)):
                raise ConflictError('Cancellazione non consentita: ingressi registrati')
            # A stored purchase is financial history even after refund/status changes.
            for field in ('ref_id', 'event_id'):
                query = db.collection('purchases').where(filter=FieldFilter(field, '==', event_id))
                if list(query.limit(1).stream(transaction=transaction)):
                    raise ConflictError('Cancellazione non consentita: acquisti collegati')
            holds = list(db.collection('event_capacity').document(event_id).collection('reservations')
                         .stream(transaction=transaction))
            now = datetime.now(timezone.utc)
            for hold in holds:
                data = hold.to_dict() or {}
                expires = data.get('expiresAt')
                if (data.get('orderId') or data.get('purchaseId')
                        or data.get('state') != 'released' and not (
                            data.get('state') == 'reserved' and isinstance(expires, datetime)
                            and expires.tzinfo is not None and expires <= now)):
                    raise ConflictError('Cancellazione non consentita: prenotazione o pagamento da verificare')
            deletes.extend(doc.reference for doc in holds)
            # Retain orders for reconciliation; never orphan even an unpaid provider order.
            if list(db.collection('orders').where(filter=FieldFilter('eventId', '==', event_id))
                    .limit(1).stream(transaction=transaction)):
                raise ConflictError('Cancellazione non consentita: ordini collegati')
            tokens = db.collection('scan_tokens').where(filter=FieldFilter('event_id', '==', event_id))
            deletes.extend(doc.reference for doc in tokens.stream(transaction=transaction))
            members = db.collection('memberships').where(filter=FieldFilter('attended_events', 'array_contains', event_id))
            membership_updates.extend(doc.reference for doc in members.stream(transaction=transaction))
            for collection in ('event_locations', 'event_guides', 'analytics_event',
                               'participants', 'entrance_scans', 'event_capacity'):
                deletes.append(db.collection(collection).document(event_id))
            deletes.append(event_ref)
        # Keep cleanup atomic; a larger event needs an explicitly reviewed bulk operation.
        if len(deletes) + len(membership_updates) + (participant_id is not None) > 400:
            raise ConflictError('Troppi riferimenti per la cancellazione atomica: gestione manuale richiesta')
        for ref in membership_updates:
            transaction.update(ref, {'attended_events': firestore.ArrayRemove([event_id])})
        for ref in deletes:
            transaction.delete(ref)
        if participant_id is not None:
            transaction.update(event_ref, {'capacityRevision': firestore.Increment(1)})

    remove(db.transaction())
