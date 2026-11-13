"""Manual receipts are per participant; linked website payments are never added twice."""
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from models import Event, EventParticipant, EventPurchase, PaymentMethod
from services.core.analytics_service import AnalyticsService
from services.core.stats_service import StatsService


def services(participants, purchases=()):
    event = Event(id='event-1',title='Synthetic',date=(datetime.now()+timedelta(days=1)).strftime('%d-%m-%Y'),max_participants=100)
    events = SimpleNamespace(stream_models=lambda:iter([event]),get_model=lambda _:event)
    members = SimpleNamespace(stream=lambda:iter(()),get_last_by_start_date=lambda:None)
    purchase_repo = SimpleNamespace(stream_models=lambda:iter(purchases),
        list_models_by_ref_id=lambda event_id:[p for p in purchases if p.ref_id==event_id],get_last_by_timestamp=lambda:None)
    people = SimpleNamespace(stream_all=lambda:iter(participants),
        list=lambda event_id:[p for p in participants if p.event_id==event_id],get_last_across_events=lambda:None)
    general = StatsService(event_repository=events,membership_repository=members,purchase_repository=purchase_repo,
        participant_repository=people,message_repository=SimpleNamespace(count_unanswered_since=lambda _:0,get_last_model=lambda:None))
    analytics = AnalyticsService(event_repository=events,membership_repository=members,purchase_repository=purchase_repo,
        participant_repository=people,entrance_scan_repository=SimpleNamespace())
    return general,analytics


def person(price=10,method=PaymentMethod.CASH,link=None,event='event-1'):
    return EventParticipant(event_id=event,price=price,payment_method=method,purchase_id=link)


def test_mixed_receipts_keep_online_net_and_fees_separate_without_double_counting():
    purchase = EventPurchase(id='purchase-1',ref_id='event-1',participants_count=2,
        status='COMPLETED',capture_status='COMPLETED',amount_total='44',net_amount='42.50')
    participants = [person(1000,PaymentMethod.WEBSITE,'purchase-1'),person(999,PaymentMethod.CASH,'purchase-1'),
        person(10),person('20.50',PaymentMethod.IBAN),person(5,PaymentMethod.PRIVATE_PAYPAL),
        person(500,PaymentMethod.OMAGGIO),person(999,PaymentMethod.WEBSITE),person(999,PaymentMethod.CASH,'orphan')]
    general,analytics = services(participants,[purchase])
    payload = general.get_general_stats()
    assert (payload['total_gross_amount'],payload['total_net_amount']) == ('44.00','42.50')
    assert (payload['total_manual_amount'],payload['total_received_amount']) == ('35.50','79.50')
    assert payload['upcoming_event_total_paid'] == '79.50'
    event = analytics.get_revenue_breakdown('event-1').model_dump(by_alias=True)
    assert (event['totalGross'],event['totalNet'],event['paypalFees']) == (44,42.5,1.5)
    assert (event['manualReceived'],event['totalReceived']) == (35.5,79.5)
    assert sum(tier['count'] for tier in event['byTier']) == 2
    dashboard = analytics.get_dashboard_kpis().model_dump(by_alias=True)
    assert dashboard['totalRevenueNet'] == 42.5
    assert (dashboard['manualReceived'],dashboard['totalReceived']) == (35.5,79.5)
    assert dashboard['totalOmaggi'] == 1


@pytest.mark.parametrize('method', [PaymentMethod.CASH,PaymentMethod.IBAN,PaymentMethod.PRIVATE_PAYPAL,' CASH ','iban','private_paypal'])
def test_explicit_manual_methods_are_received(method):
    general,analytics = services([person('12.50',method)])
    assert general.get_general_stats()['total_manual_amount'] == '12.50'
    assert analytics.get_revenue_breakdown('event-1').model_dump(by_alias=True)['manualReceived'] == 12.5


@pytest.mark.parametrize('method', [PaymentMethod.WEBSITE,PaymentMethod.OMAGGIO,None,'unknown',''])
def test_other_methods_do_not_become_manual_income(method):
    general,_ = services([person(10,method)])
    assert general.get_general_stats()['total_manual_amount'] == '0.00'


@pytest.mark.parametrize('link', ['purchase-1','missing-purchase',' ',0,False])
def test_any_nonempty_or_malformed_reference_prevents_manual_fallback(link):
    general,_ = services([person(10,link=link)])
    assert general.get_general_stats()['total_manual_amount'] == '0.00'


@pytest.mark.parametrize('amount', [0,-10,None,True,'not-money','12,50','NaN','Infinity','-Infinity','1.001',Decimal('NaN')])
def test_invalid_zero_or_noncent_amounts_do_not_create_manual_receipts(amount):
    general,_ = services([person(amount)])
    assert general.get_general_stats()['total_manual_amount'] == '0.00'


def test_cent_sums_are_exact_and_the_upcoming_event_excludes_other_events():
    general,analytics = services([person('0.10'),person('0.20'),person('50.00',event='other-event')])
    result = general.get_general_stats()
    assert result['total_manual_amount'] == '50.30'
    assert result['total_received_amount'] == '50.30'
    assert result['upcoming_event_total_paid'] == '0.30'
    assert analytics.get_revenue_breakdown('event-1').model_dump(by_alias=True)['manualReceived'] == .3


@pytest.mark.parametrize('method,expected', [
    (' CASH ','12.50'),('IBAN','12.50'),(' PRIVATE_PAYPAL ','12.50'),
    (' OMAGGIO ','0.00'),(' WEBSITE ','0.00'),('unknown','0.00'),
])
def test_stored_methods_are_normalized_before_enum_decoding_without_changing_source(method, expected):
    data = {'event_id':'event-1','price':'12.50','payment_method':method}
    participant = EventParticipant.from_firestore(data,'legacy-receipt')
    general,_ = services([participant])
    assert general.get_general_stats()['total_manual_amount'] == expected
    assert data['payment_method'] == method
    if method.strip().lower() == 'omaggio':
        assert participant.payment_method is PaymentMethod.OMAGGIO
