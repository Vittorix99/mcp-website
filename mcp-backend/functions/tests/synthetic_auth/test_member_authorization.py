"""OPS-01: real emulator tokens, personal ownership and no unauthorized writes."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local

import pytest
from google.cloud.firestore_v1.document import DocumentReference

from config.firebase_config import db
from errors.service_errors import ValidationError
from repositories.membership_repository import MembershipRepository

ROUTES = ('/me', '/events', '/purchases', '/ticket', '/preferences')


def call(http, route, token=None):
    headers = {'Authorization': 'Bearer ' + token} if token is not None else {}
    if route == '/preferences':
        return http.patch(route, json={'newsletter_consent': False}, headers=headers)
    return http.get(route, query_string={'event_id': 'private-event'}, headers=headers)


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('actor,binding,expected', [
    ('owner', None, 200), ('unverified', None, 401), ('owner', 'other', 401),
    ('owner', 'self', 200), ('unverified', 'self', 200),
])
def test_identity_matrix_for_every_personal_route(http, accounts, seed_member, route, actor, binding, expected):
    account = getattr(accounts, actor)
    uid = account.uid if binding == 'self' else accounts.admin.uid if binding == 'other' else None
    ref = seed_member(account, uid)
    before = ref.get().to_dict()
    response = call(http, route, account.token)
    assert response.status_code == expected, response.get_json()
    if expected == 401:
        assert ref.get().to_dict() == before
        assert 'private' not in response.get_data(as_text=True).lower()
    else:
        wanted = {**before, 'uid': account.uid}
        if route == '/preferences':
            wanted['newsletter_consent'] = False
        assert ref.get().to_dict() == wanted
        if route == '/me':
            assert response.get_json()['id'] == ref.id
        elif route == '/events':
            assert [item['id'] for item in response.get_json()] == ['private-event']
        elif route == '/purchases':
            assert [item['id'] for item in response.get_json()] == ['private-purchase']
        elif route == '/ticket':
            assert response.get_json()['ticket_pdf_url'] == 'https://example.invalid/private-ticket'


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('token', [None, 'not-a-valid-token'])
def test_missing_or_invalid_token_exposes_nothing(http, accounts, seed_member, route, token):
    ref = seed_member(accounts.owner, accounts.owner.uid)
    before = ref.get().to_dict()
    response = call(http, route, token)
    assert response.status_code == 401
    assert 'private' not in response.get_data(as_text=True).lower()
    assert ref.get().to_dict() == before


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('actor,expected', [('owner', 404), ('unverified', 401)])
def test_no_membership_does_not_allow_access_or_email_enumeration(http, accounts, route, actor, expected):
    response = call(http, route, getattr(accounts, actor).token)
    assert response.status_code == expected, response.get_json()
    assert list(db.collection('memberships').stream()) == []


@pytest.mark.parametrize('actor,expected', [('owner', 401), ('unverified', 401), ('admin', 201), (None, 401)])
def test_admin_write_requires_actual_admin_claim(http, accounts, seed_member, actor, expected):
    seed_member(accounts.owner, accounts.owner.uid)
    headers = {'Authorization': 'Bearer ' + getattr(accounts, actor).token} if actor else {}
    response = http.post('/admin-token', json={'event_id': 'private-event'}, headers=headers)
    assert response.status_code == expected, response.get_data(as_text=True)
    assert len(list(db.collection('scan_tokens').stream())) == (1 if expected == 201 else 0)


def test_public_events_remain_public(http, accounts, seed_member):
    seed_member(accounts.owner, accounts.owner.uid)
    assert http.get('/public-events').status_code == 200


def test_admin_uses_admin_routes_for_other_members_not_personal_identity_bypass(http, accounts, seed_member):
    ref = seed_member(accounts.admin, accounts.owner.uid)
    before = ref.get().to_dict()
    assert call(http, '/me', accounts.admin.token).status_code == 401
    assert ref.get().to_dict() == before


def test_failed_first_binding_does_not_return_profile(http, accounts, seed_member, monkeypatch):
    ref = seed_member(accounts.owner, None)
    before = ref.get().to_dict()
    original = DocumentReference.update
    def fail(target, data, *args, **kwargs):
        if target.path == ref.path and 'uid' in data:
            raise RuntimeError('Synthetic binding persistence failure')
        return original(target, data, *args, **kwargs)
    monkeypatch.setattr(DocumentReference, 'update', fail)
    response = call(http, '/me', accounts.owner.token)
    assert response.status_code == 500
    assert 'private' not in response.get_data(as_text=True).lower()
    assert ref.get().to_dict() == before


@pytest.mark.parametrize('field', ['uid', 'email'])
def test_preferences_cannot_restore_stale_ownership(http, accounts, seed_member, monkeypatch, field):
    ref = seed_member(accounts.owner, accounts.owner.uid)
    original_update, original_set = DocumentReference.update, DocumentReference.set
    switched = []
    replacement = accounts.admin.uid if field == 'uid' else accounts.admin.email
    def before_write(target, data):
        if target.path == ref.path and 'newsletter_consent' in data and not switched:
            switched.append(True)
            original_update(target, {field: replacement})
    def update(target, data, *args, **kwargs):
        before_write(target, data)
        return original_update(target, data, *args, **kwargs)
    def set_data(target, data, *args, **kwargs):
        before_write(target, data)
        return original_set(target, data, *args, **kwargs)
    monkeypatch.setattr(DocumentReference, 'update', update)
    monkeypatch.setattr(DocumentReference, 'set', set_data)
    response = call(http, '/preferences', accounts.owner.token)
    assert response.status_code == 401, response.get_json()
    after = ref.get().to_dict()
    assert after[field] == replacement and after['newsletter_consent'] is True


def test_two_repository_claims_cannot_replace_each_other(accounts, seed_member, monkeypatch):
    # Exercise the storage primitive with trusted identity inputs; HTTP claim tests above use real JWTs.
    ref = seed_member(accounts.owner, None)
    original = DocumentReference.update
    ready, once = Barrier(2, timeout=10), local()
    def update(target, data, *args, **kwargs):
        if target.path == ref.path and 'uid' in data and not getattr(once, 'waited', False):
            once.waited = True
            ready.wait()
        return original(target, data, *args, **kwargs)
    monkeypatch.setattr(DocumentReference, 'update', update)
    repo = MembershipRepository()
    def claim(uid):
        try:
            return repo.get_for_account(accounts.owner.email, uid, allow_link=True).uid
        except ValidationError:
            return 'rejected'
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(claim, [accounts.owner.uid, accounts.admin.uid]))
    winner = ref.get().to_dict()['uid']
    assert outcomes.count('rejected') == 1 and outcomes.count(winner) == 1



def test_ambiguous_email_cannot_bind_an_arbitrary_membership(http, accounts, seed_member):
    ref = seed_member(accounts.owner, None)
    second = db.document('memberships/ambiguous-member')
    second.set(ref.get().to_dict())
    response = call(http, '/me', accounts.owner.token)
    assert response.status_code == 401, response.get_json()
    assert ref.get().to_dict()['uid'] is None
    assert second.get().to_dict()['uid'] is None



def test_preferences_cannot_follow_reassigned_email_to_another_profile(http, accounts, seed_member, monkeypatch):
    ref = seed_member(accounts.owner, accounts.owner.uid)
    replacement = db.document('memberships/replacement-profile')
    before = ref.get().to_dict()
    other = {**before, 'uid': None, 'name': 'Different private owner'}
    original = DocumentReference.update
    switched = []
    def update(target, data, *args, **kwargs):
        if target.path == ref.path and 'newsletter_consent' in data and not switched:
            switched.append(True)
            original(target, {'email': accounts.admin.email})
            replacement.set(other)
        return original(target, data, *args, **kwargs)
    monkeypatch.setattr(DocumentReference, 'update', update)
    response = call(http, '/preferences', accounts.owner.token)
    assert response.status_code == 401, response.get_json()
    assert replacement.get().to_dict() == other
