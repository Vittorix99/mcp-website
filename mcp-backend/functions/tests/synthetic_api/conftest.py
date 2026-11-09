"""Small isolated HTTP-handler scenarios; never run against cloud or bulk data."""
import json
import importlib.util
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.request import ProxyHandler, build_opener

import pytest
from flask import Flask, request

from config.firebase_config import db
from models import Event, EventParticipant, EventPurchase, Membership, PaymentMethod
from api.admin import purchases_api, stats_api
from api.entrance import entrance_api
from api.public import event_payment_api
from services.payments.event_payment_service import EventPaymentService
from services.payments.paypal_gateway import FakePayPalGateway, PayPalGatewayResponse

ROOT = Path(__file__).resolve().parents[4]
_spec = importlib.util.spec_from_file_location('synthetic_loader', ROOT / 'scripts/staging/load_emulator.py')
_loader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_loader)
_document_paths = _loader._document_paths
validate_emulators = _loader.validate_emulators
validate_target = _loader.validate_target


@pytest.fixture(scope='session', autouse=True)
def isolated_emulator():
    if os.environ.get('SYNTHETIC_API_TESTS') != '1':
        pytest.fail('Run scripts/staging/test_emulator.py --api; no emulator auto-detection')
    host = validate_target(db.project, os.environ.get('FIRESTORE_EMULATOR_HOST', ''))
    hub = validate_target(db.project, os.environ.get('FIREBASE_EMULATOR_HUB', ''))
    assert db._emulator_host == host
    with build_opener(ProxyHandler({})).open(f'http://{hub}/emulators', timeout=5) as response:
        validate_emulators(json.load(response), host)
    assert not _document_paths(db), 'Scenarios require an empty dedicated emulator, not the bulk dataset'


@pytest.fixture(autouse=True)
def clean_case_database(isolated_emulator):
    # Only this suite's documents, in the previously verified dedicated demo emulator.
    before = _document_paths(db)
    assert not before, 'Previous scenario left data behind'
    yield
    paths = _document_paths(db) - before
    for offset in range(0, len(paths), 400):
        batch = db.batch()
        for path in sorted(paths)[offset:offset + 400]:
            batch.delete(db.document(path))
        batch.commit(timeout=20)


@pytest.fixture
def http():
    app = Flask('synthetic-api-scenarios')
    handlers = {
        '/orders': event_payment_api.create_order_event,
        '/capture': event_payment_api.capture_order_event,
        '/purchase-status': purchases_api.update_purchase_status,
        '/revenue': stats_api.admin_get_revenue_breakdown,
        '/funnel': stats_api.admin_get_event_funnel,
        '/general': stats_api.admin_get_general_stats,
        '/snapshot': stats_api.admin_get_analytics_event_snapshot,
        '/scanner-token': entrance_api.entrance_generate_scan_token,
        '/verify-token': entrance_api.entrance_verify_scan_token,
        '/scan': entrance_api.entrance_validate,
        '/manual-entry': entrance_api.entrance_manual_entry,
    }
    for index, (path, handler) in enumerate(handlers.items()):
        def route(handler=handler):
            return handler(request)
        app.add_url_rule(path, f'endpoint-{index}', route, methods=['GET', 'POST'])
    app.config['TESTING'] = True
    client = app.test_client()
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer synthetic-test-admin'
    return client


@pytest.fixture
def sample():
    now = datetime.now(timezone.utc)
    event = Event(id='case-event', title='Evento inventato', date=(now + timedelta(days=2)).strftime('%d-%m-%Y'),
                  start_time='22:00', end_time='06:00', price=20.0, fee=2.0, max_participants=10)
    db.document('events/' + event.id).set(event.to_firestore())
    people = []
    for suffix in ('a', 'b'):
        member = Membership(id=f'case-member-{suffix}', name='Mario' if suffix == 'a' else 'Elena',
                            surname='Prova', email=f'scenario-{suffix}@example.com', phone=f'+999000{suffix}',
                            birthdate='10-01-1985', start_date=now.isoformat(), end_date=f'31-12-{now.year}',
                            subscription_valid=True, membership_years=[now.year], send_card_on_create=False)
        db.document('memberships/' + member.id).set(member.to_firestore())
        people.append(member)
    return SimpleNamespace(event=event, people=people, now=now)


@pytest.fixture
def completed(sample):
    purchase = EventPurchase(id='case-purchase', payer_name='Pagante', payer_surname='Inventato',
                            payer_email='payer@example.com', amount_total='44.00', currency='EUR',
                            paypal_fee='1.50', net_amount='42.50', transaction_id='SYNTHETIC-CAPTURE',
                            order_id='SYNTHETIC-ORDER', status='COMPLETED', capture_status='COMPLETED',
                            timestamp=sample.now.isoformat(), ref_id=sample.event.id, event_id=sample.event.id,
                            participants_count=2, membership_ids=[m.id for m in sample.people], payment_method='paypal')
    db.document('purchases/' + purchase.id).set(purchase.to_firestore())
    for member in sample.people:
        participant = EventParticipant(id=member.id, event_id=sample.event.id, name=member.name,
                                       surname=member.surname, email=member.email, phone=member.phone,
                                       birthdate=member.birthdate, membership_id=member.id,
                                       purchase_id=purchase.id, price=20.0, payment_method=PaymentMethod.WEBSITE,
                                       send_ticket_on_create=False, created_at=sample.now)
        db.document(f'participants/{sample.event.id}/participants_event/{member.id}').set(participant.to_firestore())
    sample.purchase = purchase
    return sample


class ControlledGateway(FakePayPalGateway):
    """Provider responses under test control; no SDK/network/provider endpoint."""
    def __init__(self):
        super().__init__()
        self.capture_calls = 0
        self.bad_field = None
        self.bad_state = None

    def capture_order(self, order_id):
        self.capture_calls += 1
        response = super().capture_order(order_id)
        body = response.payload
        if response.status_code == 201:
            capture = body['purchase_units'][0]['payments']['captures'][0]
            capture['create_time'] = datetime.now(timezone.utc).isoformat()
            capture['seller_receivable_breakdown']['paypal_fee']['value'] = '1.50'
            capture['seller_receivable_breakdown']['net_amount']['value'] = '42.50'
            if self.bad_field == 'status':
                body['status'] = self.bad_state
            elif self.bad_field == 'capture_status':
                capture['status'] = self.bad_state
        return PayPalGatewayResponse(response.status_code, body)


@pytest.fixture
def gateway(monkeypatch):
    fake = ControlledGateway()
    monkeypatch.setattr(event_payment_api, 'event_payment_service', EventPaymentService(paypal_gateway=fake))
    return fake
