"""Explicit Auth+Firestore mode; no token-verifier bypass in this suite."""
import json
import os
from types import SimpleNamespace
from urllib.request import Request, ProxyHandler, build_opener
from uuid import uuid4

import firebase_admin.auth as firebase_auth
from flask import Flask, request
import pytest

from api.member import member_api
from api.entrance import entrance_api
from api.public import events_api
from config.firebase_config import db
from models import Event, EventParticipant, EventPurchase, Membership
from tests.synthetic_api.conftest import isolated_emulator, clean_case_database

SDK_VERIFY = firebase_auth.verify_id_token
PASSWORD = 'Synthetic-only-123!'  # NOSECRET: emulator-only fixed fixture


@pytest.fixture(autouse=True)
def _bypass_admin_auth():
    # Override the parent fixture with a no-op, keeping Firebase's actual verifier.
    assert firebase_auth.verify_id_token is SDK_VERIFY
    yield


@pytest.fixture(scope='session')
def accounts(isolated_emulator):
    assert os.environ.get('SYNTHETIC_AUTH_TESTS') == '1'
    assert os.environ['FIREBASE_AUTH_EMULATOR_HOST'] == '127.0.0.1:9190'
    assert db.project == 'demo-mcp-test'
    with build_opener(ProxyHandler({})).open('http://127.0.0.1:4480/emulators', timeout=5) as response:
        emulators = json.load(response)
    assert emulators['auth']['host'] == '127.0.0.1' and emulators['auth']['port'] == 9190
    users = []
    def create(verified, admin=False):
        account = firebase_auth.create_user(email=f'ops-auth-{uuid4().hex}@example.com',
            password=PASSWORD, email_verified=verified)  # NOSECRET: emulator-only fixture
        users.append(account.uid)
        if admin:
            firebase_auth.set_custom_user_claims(account.uid, {'admin': True})
        body = json.dumps({'email': account.email, 'password': PASSWORD,
                           'returnSecureToken': True}).encode()  # NOSECRET: emulator-only fixture
        req = Request('http://127.0.0.1:9190/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-key',
                      data=body, headers={'Content-Type': 'application/json'})
        with build_opener(ProxyHandler({})).open(req, timeout=5) as response:
            token = json.load(response)['idToken']
        claims = SDK_VERIFY(token)
        assert claims['uid'] == account.uid and claims['email_verified'] is verified
        return SimpleNamespace(uid=account.uid, email=account.email, token=token)
    try:
        yield SimpleNamespace(owner=create(True), unverified=create(False), admin=create(True, True))
    finally:
        for uid in users:
            firebase_auth.delete_user(uid)


@pytest.fixture
def http():
    app = Flask('synthetic-member-auth')
    routes = [
        ('/me', 'GET', member_api.member_get_me),
        ('/events', 'GET', member_api.member_get_events),
        ('/purchases', 'GET', member_api.member_get_purchases),
        ('/ticket', 'GET', member_api.member_get_ticket),
        ('/preferences', 'PATCH', member_api.member_patch_preferences),
        ('/admin-token', 'POST', entrance_api.entrance_generate_scan_token),
        ('/public-events', 'GET', events_api.get_all_events),
    ]
    for index, (path, method, handler) in enumerate(routes):
        app.add_url_rule(path, f'route-{index}', lambda handler=handler: handler(request), methods=[method])
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def seed_member():
    def seed(account, uid):
        event = Event(id='private-event', title='Private fixture event', date='01-01-2099')
        db.document('events/' + event.id).set(event.to_firestore())
        purchase = EventPurchase(id='private-purchase', event_id=event.id, ref_id=event.id,
            amount_total='44.00', currency='EUR', participants_count=1)
        db.document('purchases/' + purchase.id).set(purchase.to_firestore())
        member = Membership(id='private-member', name='Private profile marker', surname='Synthetic',
            email=account.email, uid=uid, subscription_valid=False, membership_years=[],
            newsletter_consent=True, attended_events=[event.id], purchases=[purchase.id],
            wallet_url='https://example.invalid/private-wallet', card_url='https://example.invalid/private-card')
        ref = db.document('memberships/' + member.id)
        ref.set(member.to_firestore(include_none=True))
        person = EventParticipant(id='private-person', event_id=event.id, membership_id=member.id,
            purchase_id=purchase.id, ticket_pdf_url='https://example.invalid/private-ticket')
        db.document(f'participants/{event.id}/participants_event/{person.id}').set(person.to_firestore())
        return ref
    return seed
