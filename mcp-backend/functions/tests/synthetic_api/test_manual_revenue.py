"""Received off-site payments, gifts and linked purchases across HTTP reports/snapshots."""
from datetime import timedelta

import pytest

from config.firebase_config import db
from models import EventParticipant, PaymentMethod
from services.core.analytics_service import AnalyticsService
from services.core.analytics_snapshot_service import AnalyticsSnapshotService


@pytest.mark.parametrize('stored_methods', ['canonical','legacy-case'])
@pytest.mark.parametrize('capture_state,online_gross,online_net', [
    ('COMPLETED',44,42.5),('PENDING',0,0),('DECLINED',0,0),(None,0,0),
])
def test_manual_receipts_do_not_duplicate_even_an_unconfirmed_linked_purchase(http, completed, capture_state, online_gross, online_net, stored_methods):
    event_id = completed.event.id
    purchase = db.document('purchases/' + completed.purchase.id)
    purchase.update({'capture_status':capture_state})
    people = db.collection(f'participants/{event_id}/participants_event')
    for index,(method,price,link) in enumerate([
        (PaymentMethod.CASH,10,None), (PaymentMethod.IBAN,20.5,''),
        (PaymentMethod.PRIVATE_PAYPAL,5,None), (PaymentMethod.OMAGGIO,99,None),
        (PaymentMethod.WEBSITE,500,None), (PaymentMethod.CASH,500,completed.purchase.id),
        (PaymentMethod.CASH,600,'missing-purchase'),
    ]):
        if stored_methods == 'legacy-case':
            method = ' ' + method.value.upper() + ' '
        person = EventParticipant(id=f'manual-{index}',event_id=event_id,name='Synthetic',surname='Receipt',
            price=price,payment_method=method,purchase_id=link,send_ticket_on_create=False,
            created_at=completed.now+timedelta(seconds=index+1))
        people.document(person.id).set(person.to_firestore())
    before_people = {row.id:row.to_dict() for row in people.stream()}
    before_purchase = purchase.get().to_dict()
    assert len(before_people) == 9
    total_received = online_gross + 35.5
    response = http.get('/general')
    assert response.status_code == 200, response.get_json()
    general = response.get_json()
    assert (general['total_gross_amount'],general['total_net_amount']) == (f'{online_gross:.2f}',f'{online_net:.2f}')
    assert (general['total_manual_amount'],general['total_received_amount']) == ('35.50',f'{total_received:.2f}')
    assert general['upcoming_event_total_paid'] == f'{total_received:.2f}'
    event_response = http.get('/revenue',query_string={'event_id':event_id})
    assert event_response.status_code == 200, event_response.get_json()
    event = event_response.get_json()
    assert (event['totalGross'],event['totalNet'],event['paypalFees']) == (online_gross,online_net,online_gross-online_net)
    assert (event['manualReceived'],event['totalReceived']) == (35.5,total_received)
    dashboard = AnalyticsService().get_dashboard_kpis().model_dump(by_alias=True)
    assert (dashboard['manualReceived'],dashboard['totalReceived']) == (35.5,total_received)
    snapshots = AnalyticsSnapshotService()
    for _ in range(2):
        event = snapshots.rebuild_event_snapshot(event_id)['kpis']
        assert (event['revenue_gross'],event['revenue_net']) == (online_gross,online_net)
        assert (event['manual_received'],event['total_received']) == (35.5,total_received)
        assert (event['participants'],event['omaggi']) == (9,1)
        global_kpis = snapshots.rebuild_global_snapshot()['kpis']
        assert (global_kpis['manual_received'],global_kpis['total_received']) == (35.5,total_received)
        dashboard_kpis = snapshots.rebuild_dashboard_snapshot()['kpis']
        assert (dashboard_kpis['manual_received'],dashboard_kpis['total_received']) == (35.5,total_received)
        assert dashboard_kpis['total_revenue_net'] == online_net
    assert {row.id:row.to_dict() for row in people.stream()} == before_people
    assert purchase.get().to_dict() == before_purchase
    assert not list(db.collection(f'entrance_scans/{event_id}/scans').stream())
