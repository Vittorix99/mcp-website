"""Only confirmed order AND capture states contribute to online purchase metrics."""
from types import SimpleNamespace

import pytest

from models import EventPurchase, Purchase, PurchaseStatus, PurchaseTypes
from services.core.analytics_service import AnalyticsService
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from services.core.stats_service import StatsService


def general_stats(purchases, recent=None):
    return StatsService(
        event_repository=SimpleNamespace(stream_models=lambda:iter(())),
        membership_repository=SimpleNamespace(stream=lambda:iter(()),get_last_by_start_date=lambda:None),
        purchase_repository=SimpleNamespace(stream_models=lambda:iter(purchases),get_last_by_timestamp=lambda:recent),
        participant_repository=SimpleNamespace(get_last_across_events=lambda:None,stream_all=lambda:iter(())),
        message_repository=SimpleNamespace(count_unanswered_since=lambda _:0,get_last_model=lambda:None),
    ).get_general_stats()


@pytest.mark.parametrize('field', ['status', 'capture_status'])
@pytest.mark.parametrize('state', [
    'FAILED','CANCELLED','VOIDED','REFUNDED','DECLINED','ERROR',
    'PENDING','CREATED','APPROVED','CAPTURED','UNKNOWN','',None,17,True,' COMPLETED ',
])
def test_unconfirmed_state_is_excluded_from_all_three_statistics_services(field, state):
    purchase = EventPurchase(status='COMPLETED',capture_status='COMPLETED',ref_id='event-1',
        participants_count=2,amount_total='44.00',net_amount='42.50')
    setattr(purchase, field, state)
    general = general_stats([purchase])
    assert general['total_purchases'] == 0
    assert general['total_gross_amount'] == '0.00'
    assert general['total_net_amount'] == '0.00'
    assert AnalyticsService.__new__(AnalyticsService)._is_valid_event_purchase(purchase) is False
    assert AnalyticsSnapshotService.__new__(AnalyticsSnapshotService)._is_valid_event_purchase(purchase) is False


@pytest.mark.parametrize('state', ['COMPLETED','completed',PurchaseStatus.COMPLETED])
def test_confirmed_purchase_counts_once_with_two_tickets(state):
    purchase = EventPurchase(status=state,capture_status=state,ref_id='event-1',
        participants_count=2,amount_total='44.00',net_amount='42.50')
    general = general_stats([purchase])
    assert general['total_purchases'] == 1
    assert general['total_gross_amount'] == '44.00'
    assert general['total_net_amount'] == '42.50'
    assert AnalyticsService.__new__(AnalyticsService)._is_valid_event_purchase(purchase) is True
    assert AnalyticsSnapshotService.__new__(AnalyticsSnapshotService)._is_valid_event_purchase(purchase) is True


@pytest.mark.parametrize('invalid_event_field', [
    {'ref_id':None}, {'participants_count':0}, {'purchase_type':PurchaseTypes.MEMBERSHIP},
])
def test_event_specific_requirements_remain_separate_from_general_purchase_totals(invalid_event_field):
    purchase = EventPurchase(status='COMPLETED',capture_status='COMPLETED',ref_id='event-1',
        participants_count=2,amount_total='44.00',net_amount='42.50')
    for field, value in invalid_event_field.items():
        setattr(purchase, field, value)
    assert general_stats([purchase])['total_purchases'] == 1
    assert AnalyticsService.__new__(AnalyticsService)._is_valid_event_purchase(purchase) is False
    assert AnalyticsSnapshotService.__new__(AnalyticsSnapshotService)._is_valid_event_purchase(purchase) is False


def test_general_totals_include_confirmed_membership_purchases_without_event_fields():
    purchase = Purchase(status='COMPLETED',capture_status='COMPLETED',purchase_type=PurchaseTypes.MEMBERSHIP,
        amount_total='20.00',net_amount='19.00')
    general = general_stats([purchase])
    assert general['total_purchases'] == 1
    assert general['total_gross_amount'] == '20.00'
    assert general['total_net_amount'] == '19.00'


def test_null_status_recent_purchase_remains_visible_but_does_not_count_as_revenue():
    purchase = Purchase(id='incomplete-purchase',status=None,capture_status='COMPLETED',
        amount_total='100.00',net_amount='90.00')
    general = general_stats([purchase], recent=purchase)
    assert (general['total_purchases'],general['total_gross_amount']) == (0,'0.00')
    assert general['last_purchase']['id'] == 'incomplete-purchase'
    assert general['last_purchase']['status'] == ''
    assert purchase.status is None
