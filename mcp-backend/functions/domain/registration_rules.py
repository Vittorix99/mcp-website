"""One nominative registration per event, including unfinished checkouts."""
from hashlib import sha256

from errors.service_errors import ConflictError
from utils.events_utils import normalize_email, normalize_phone


def registration_keys(data):
    values = {'email': normalize_email(data.get('email') or ''),
              'phone': normalize_phone(data.get('phone') or ''),
              'membership': data.get('membershipId')}
    return {sha256(f'{kind}:{value}'.encode()).hexdigest() for kind, value in values.items() if value}


def checkout_keys(participants, lookup):
    keys = set()
    for participant in participants:
        member = lookup.get(normalize_email(participant.get('email') or ''), {})
        current = (registration_keys({**participant, 'membershipId': member.get('id')})
                   | registration_keys({**member, 'membershipId': member.get('id')}))
        if current & keys:
            raise ConflictError('Una sola iscrizione per persona e per evento')
        keys.update(current)
    return keys


def assert_registration_available(keys, people, holds, now, *, own_token=None):
    if any(keys & registration_keys(person) for person in people):
        raise ConflictError('Partecipante già iscritto a questo evento')
    for token, hold in holds:
        if token == own_token or hold.get('state') in ('consumed', 'released'):
            continue
        if hold.get('state') == 'reserved':
            expiry = hold.get('expiresAt')
            if expiry is not None and getattr(expiry, 'tzinfo', None) is not None and expiry <= now:
                continue
        reserved = hold.get('identityKeys')
        if not isinstance(reserved, list) or not reserved or any(not isinstance(key, str) for key in reserved):
            raise ConflictError('Identità della prenotazione non verificabile: gestione manuale richiesta')
        if keys & set(reserved):
            raise ConflictError('Partecipante già incluso in un checkout in corso')
