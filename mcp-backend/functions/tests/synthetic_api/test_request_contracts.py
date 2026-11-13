"""OPS-02: real Flask parsing and emulator state, with fake payment providers."""
import pytest
from flask import request

from api.admin import events_api, participants_api
from api.member import member_api
from config.firebase_config import db
from tests.synthetic_api.conftest import _document_paths
from tests.synthetic_api.test_purchase_entrance_stats import order_payload


def database_state():
    return {path: db.document(path).get().to_dict() for path in sorted(_document_paths(db))}


@pytest.mark.parametrize('body', [
    '', '{', 'null', '{}', '[]', '[1]', '"payload"', '1', 'true',
    '{"cart":null}', '{"cart":{}}', '{"cart":[]}',
    '{"cart":[{},{}]}', '{"cart":[1]}', '{"cart":["item"]}',
    '{"cart":[true]}', '{"cart":[[]]}',
    '{"cart":[{"eventId":42}]}', '{"cart":[{"eventId":true}]}',
    '{"cart":[{"eventId":{}}]}', '{"cart":[{"eventId":["event"]}]}',
])
def test_checkout_invalid_json_and_shapes_return_400_without_effects(http, sample, gateway, body):
    before = database_state()
    response = http.post('/orders', data=body, content_type='application/json')
    assert response.status_code == 400, response.get_data(as_text=True)
    assert response.get_json()['error']
    assert database_state() == before
    assert (gateway.create_calls, gateway.capture_calls, gateway.read_calls) == (0, 0, 0)


@pytest.mark.parametrize('problem', ['extra_root', 'extra_person', 'email', 'participants', 'event_id'])
def test_checkout_invalid_fields_do_not_reserve_seats_or_call_provider(http, sample, gateway, problem):
    payload = order_payload(sample)
    if problem == 'extra_root':
        payload['unexpected'] = True
    elif problem == 'extra_person':
        payload['cart'][0]['participants'][0]['unexpected'] = True
    elif problem == 'email':
        payload['cart'][0]['participants'][0]['email'] = 'invalid'
    elif problem == 'participants':
        payload['cart'][0]['participants'] = []
    else:
        payload['cart'][0]['eventId'] = ' '
    before = database_state()
    response = http.post('/orders', json=payload)
    assert response.status_code == 400, response.get_json()
    assert response.get_json()['error']
    assert database_state() == before
    assert (gateway.create_calls, gateway.capture_calls, gateway.read_calls) == (0, 0, 0)


@pytest.mark.parametrize('variant', ['cart_extra', 'snake_case_id', 'trimmed_id'])
def test_checkout_supported_dto_forms_keep_the_real_price(http, sample, gateway, variant):
    payload = order_payload(sample)
    item = payload['cart'][0]
    if variant == 'cart_extra':
        item.update({'unexpected': 'ignored', 'price': 0})
    elif variant == 'snake_case_id':
        item['event_id'] = item.pop('eventId')
    else:
        item['eventId'] = ' ' + sample.event.id + ' '
    response = http.post('/orders', json=payload)
    assert response.status_code == 201, response.get_json()
    order = db.document('orders/' + response.get_json()['id']).get().to_dict()
    assert order['total'] == 44
    assert gateway.create_calls == 1
    assert gateway.capture_calls == gateway.read_calls == 0
    assert not list(db.collection('purchases').stream())


@pytest.fixture
def contract_http(http):
    for path, handler in [
        ('/event-update', events_api.admin_update_event),
        ('/participant-create', participants_api.create_participant),
        ('/participant-update', participants_api.update_participant),
        ('/preferences', member_api.member_patch_preferences),
        ('/member-ticket', member_api.member_get_ticket),
    ]:
        def route(handler=handler):
            return handler(request)
        http.application.add_url_rule(path, path, route,
                                     methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
    return http


@pytest.mark.parametrize('path,method,payload', [
    ('/event-update', 'PUT', {'id': 'case-event', 'title': 'Changed', 'unexpected': True}),
    ('/event-update', 'PUT', {'id': 'case-event', 'date': 'invalid-date'}),
    ('/participant-create', 'POST', {'eventId': 'case-event', 'email': 'invalid'}),
    ('/participant-update', 'PUT', {'eventId': 'case-event', 'participantId': 'person'}),
    ('/preferences', 'PATCH', {'newsletter_consent': False, 'unexpected': True}),
    ('/preferences', 'PATCH', {'newsletter_consent': 'invalid-boolean'}),
    ('/capture', 'POST', {'order_id': 'missing-order', 'unexpected': True}),
    ('/recover-order', 'POST', {'order_id': 'missing-order', 'unexpected': True}),
    ('/scan', 'POST', {'scan_token': 'token', 'membership_id': 'member', 'unexpected': True}),
])
def test_invalid_fields_preserve_all_documents(contract_http, sample, gateway, path, method, payload):
    before = database_state()
    response = contract_http.open(path, method=method, json=payload)
    assert response.status_code == 400, response.get_json()
    assert response.get_json()['error'] == 'Invalid request data'
    assert response.get_json()['details']
    assert database_state() == before
    assert (gateway.create_calls, gateway.capture_calls, gateway.read_calls) == (0, 0, 0)


@pytest.mark.parametrize('query', [{}, {'event_id': ''}, {'event_id': 'event', 'unexpected': 'yes'}])
def test_invalid_member_query_does_not_link_uid(contract_http, sample, query):
    before = database_state()
    response = contract_http.get('/member-ticket', query_string=query)
    assert response.status_code == 400, response.get_json()
    assert response.get_json()['details']
    assert database_state() == before


def test_participant_ignored_extra_does_not_persist_arbitrary_data(contract_http, sample):
    person = sample.people[0]
    response = contract_http.post('/participant-create', json={
        'eventId': sample.event.id, 'name': person.name, 'surname': person.surname,
        'email': person.email, 'phone': person.phone, 'birthdate': person.birthdate,
        'price': 0, 'send_ticket_on_create': False, 'unexpected': 'must not persist',
    })
    assert response.status_code == 201, response.get_json()
    participants = list(db.collection(f'participants/{sample.event.id}/participants_event').stream())
    assert len(participants) == 1
    participant = participants[0].to_dict()
    assert participant['price'] == 0
    assert participant['payment_method'] == 'omaggio'
    assert 'unexpected' not in participant
