"""Shared bounds and identity checks for atomic member/registration writes."""
from datetime import datetime, timezone

from flask import has_request_context, request
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from domain.registration_rules import assert_registration_available, registration_keys
from errors.service_errors import ConflictError, NotFoundError

IDENTITY_FIELDS = ('name', 'surname', 'email', 'phone', 'birthdate')
MAX_WRITES = 400


def identity(data):
    return {field: data.get(field) if field == 'birthdate' else (data.get(field) or '')
            for field in IDENTITY_FIELDS}


def check_write_limit(count):
    if count > MAX_WRITES:
        raise ConflictError('Operazione troppo grande: gestione manuale richiesta (limite 400 scritture)')


def operation_record(kind, **fields):
    operator = (getattr(request, 'admin_token', {}) or {}).get('uid') if has_request_context() else None
    return {'operation': kind, 'operator_uid': operator, 'created_at': firestore.SERVER_TIMESTAMP, **fields}


def registrations(member_ids, transaction):
    return list(db.collection_group('participants_event').where(
        filter=FieldFilter('membershipId', 'in', list(member_ids))).stream(transaction=transaction))


def validate_registration(event_id, data, participant_id, transaction, *, ignore_ids=()):
    event_ref = db.collection('events').document(event_id)
    event = event_ref.get(transaction=transaction)
    if not event.exists:
        raise NotFoundError('Evento non trovato')
    people = [row.to_dict() or {} for row in db.collection('participants').document(event_id)
              .collection('participants_event').stream(transaction=transaction)
              if row.id != participant_id and row.id not in ignore_ids]
    holds = [(row.id, row.to_dict() or {}) for row in db.collection('event_capacity').document(event_id)
             .collection('reservations').stream(transaction=transaction)]
    assert_registration_available(registration_keys(data), people, holds, datetime.now(timezone.utc))
    return event_ref


def contact_fences(data, transaction=None):
    """Serialize contact claims even when concurrent creations have different event IDs."""
    from hashlib import sha256
    from utils.events_utils import normalize_email, normalize_phone
    values = [('email', normalize_email(data.get('email') or '')),
              ('phone', normalize_phone(data.get('phone') or ''))]
    return [db.collection('membership_identity_fences').document(
        sha256(f'{kind}:{value}'.encode()).hexdigest()).get(transaction=transaction)
        for kind, value in values if value]


def assert_member_contacts_available(data, exclude_ids=(), transaction=None):
    for field in ('email', 'phone'):
        if not data.get(field):
            continue
        matches = db.collection('memberships').where(filter=FieldFilter(
            field, '==', data[field])).stream(transaction=transaction)
        if any(row.id not in exclude_ids for row in matches):
            raise ConflictError('Contatto già associato a un socio: selezionare la scheda esistente')


def touch_contact_fences(writer, snapshots):
    for snapshot in {row.reference.path: row for row in snapshots}.values():
        if snapshot.exists:
            writer.update(snapshot.reference, {'revision': firestore.Increment(1)},
                          option=db.write_option(last_update_time=snapshot.update_time))
        else:
            writer.create(snapshot.reference, {'revision': 1})


def assert_no_active_holds(member_data, transaction=None):
    keys = set().union(*(registration_keys(data) for data in member_data))
    now = datetime.now(timezone.utc)
    for row in db.collection_group('reservations').stream(transaction=transaction):
        hold = row.to_dict() or {}
        if hold.get('state') in ('consumed', 'released'):
            continue
        expiry = hold.get('expiresAt')
        if (hold.get('state') == 'reserved' and expiry and getattr(expiry, 'tzinfo', None)
                and expiry <= now):
            continue
        if keys.intersection(hold.get('identityKeys') or []):
            raise ConflictError('Checkout in corso: completare o risolvere prima di modificare il socio')


def prepare_identity_cascade(member_id, before, after, transaction=None):
    if identity(before) == identity(after):
        return [], {}
    assert_no_active_holds([{**before, 'membershipId': member_id},
                            {**after, 'membershipId': member_id}], transaction)
    linked = registrations([member_id], transaction)
    events = {}
    for row in linked:
        event_id = row.reference.parent.parent.id
        if event_id not in events:
            events[event_id] = db.collection('events').document(event_id).get(transaction=transaction)
        proposed = {**(row.to_dict() or {}), **identity(after)}
        validate_registration(event_id, proposed, row.id, transaction)
    return linked, events
