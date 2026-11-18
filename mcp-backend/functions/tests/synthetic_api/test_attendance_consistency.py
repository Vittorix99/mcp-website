"""Q-05: one presence total; event-time charts are only a dated subset."""
from datetime import datetime
from flask import request
import pytest

from api.admin import stats_api
from config.firebase_config import db
from dto.participant_api import ParticipantUpdateRequestDTO
from models import EventParticipant, PaymentMethod
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from services.entrance_service import EntranceService
from services.events.participants_service import ParticipantsService


@pytest.fixture
def flow_http(http):
    http.application.add_url_rule('/entrance-flow', 'q05-flow',
        lambda: stats_api.admin_get_entrance_flow(request), methods=['GET'])
    return http


def configure(sample, date='15-11-2026', start='20:15', end='01:05'):
    db.document('events/' + sample.event.id).update({'date': date, 'startTime': start, 'endTime': end})


def scan(sample, identifier, timestamp):
    db.document(f'entrance_scans/{sample.event.id}/scans/{identifier}').set({'scanned_at': timestamp})


def participant(sample, identifier, member=None, entered=False, timestamp=None):
    data = EventParticipant(name='Persona', surname='Lista', email='', phone='',
        membership_id=member, membership_included=bool(member), entered=entered,
        entered_at=timestamp, price=0, payment_method=PaymentMethod.OMAGGIO)
    ref = db.document(f'participants/{sample.event.id}/participants_event/{identifier}')
    ref.set(data.to_firestore())
    return ref


def flow(http, sample, **query):
    result = http.get('/entrance-flow', query_string={'event_id': sample.event.id, **query})
    assert result.status_code == 200, result.get_json()
    return result.get_json()


def test_scanner_funnel_snapshot_agree_including_manual_entries_and_anomalies(flow_http, sample):
    configure(sample)
    first, second = [person.id for person in sample.people]
    inside = datetime.fromisoformat('2026-11-15T20:45:00+01:00')
    participant(sample, 'linked', first, True, inside)
    participant(sample, 'legacy-duplicate', first, True, inside)
    participant(sample, 'flag-without-scan', second, True, inside)
    participant(sample, 'manual', entered=True, timestamp=inside)
    participant(sample, 'manual-unknown-time', entered=True)
    participant(sample, 'not-entered')
    scan(sample, first, inside)
    scan(sample, 'orphan', datetime.fromisoformat('2026-11-15T18:00:00+01:00'))
    funnel = flow_http.get('/funnel', query_string={'event_id': sample.event.id}).get_json()
    assert (funnel['entered'], funnel['registered'], funnel['enteredFlag'], funnel['scanned']) == (4, 5, 5, 2)
    assert funnel['showRatePct'] == 80 and funnel['scanCoveragePct'] == 50
    assert EntranceService()._build_event_counts(sample.event.id) == {'participants_count': 6, 'entered_count': 4}
    result = flow(flow_http, sample)
    assert (result['totalEntered'], result['totalScanned'], result['inWindow'],
            result['outsideWindow'], result['missingTimestamp']) == (4, 2, 2, 1, 1)
    assert result['anomalies']['missing_scan'] == 1 and result['anomalies']['orphan_scan'] == 1
    snapshot = AnalyticsSnapshotService().rebuild_event_snapshot(sample.event.id)
    assert snapshot['kpis']['entered'] == 4
    assert snapshot['attendance']['total_entered'] == 4
    assert sum(bucket['count'] for bucket in snapshot['charts']['entrance_flow']) == 2
    assert [bucket['count'] for bucket in snapshot['charts']['entrance_flow']] == [bucket['count'] for bucket in result['buckets']]


def test_chart_uses_real_dates_and_keeps_last_partial_bucket(flow_http, sample):
    configure(sample)
    timestamps = ['2026-11-14T21:00:00+01:00', '2026-11-15T20:14:59+01:00',
        '2026-11-15T20:15:00+01:00', '2026-11-15T20:44:59+01:00',
        '2026-11-15T20:45:00+01:00', '2026-11-16T01:04:59+01:00', '2026-11-16T01:05:00+01:00']
    for index, timestamp in enumerate(timestamps):
        scan(sample, str(index), datetime.fromisoformat(timestamp))
    result = flow(flow_http, sample)
    assert result['totalEntered'] == 7 and result['inWindow'] == 4 and result['outsideWindow'] == 3
    assert len(result['buckets']) == 10
    assert result['buckets'][0]['count'] == 2 and result['buckets'][1]['count'] == 1
    assert result['buckets'][-1]['count'] == 1 and result['buckets'][-1]['cumulative'] == 4
    assert result['buckets'][-1]['bucketEnd'] == '2026-11-16T01:05:00+01:00'


@pytest.mark.parametrize('end', [None, '', 'Till late'])
def test_missing_end_means_start_plus_eight_local_hours(flow_http, sample, end):
    configure(sample, start='19:10', end=end)
    scan(sample, 'inside', datetime.fromisoformat('2026-11-16T03:09:59+01:00'))
    scan(sample, 'end-exclusive', datetime.fromisoformat('2026-11-16T03:10:00+01:00'))
    result = flow(flow_http, sample)
    assert result['windowStart'] == '2026-11-15T19:10:00+01:00'
    assert result['windowEnd'] == '2026-11-16T03:10:00+01:00'
    assert result['inWindow'] == 1 and result['outsideWindow'] == 1
    assert len(result['buckets']) == 16


@pytest.mark.parametrize('date,expected', [('28-03-2026', 14), ('24-10-2026', 18)])
def test_dst_buckets_cover_real_elapsed_instants(flow_http, sample, date, expected):
    configure(sample, date=date, start='22:00', end='06:00')
    result = flow(flow_http, sample)
    assert len(result['buckets']) == expected
    starts = [datetime.fromisoformat(bucket['bucketStart']).timestamp() for bucket in result['buckets']]
    assert all(right - left == 1800 for left, right in zip(starts, starts[1:]))


def test_both_fall_back_hours_are_counted_once(flow_http, sample):
    configure(sample, date='24-10-2026', start='22:00', end='06:00')
    scan(sample, 'summer', datetime.fromisoformat('2026-10-25T02:15:00+02:00'))
    scan(sample, 'winter', datetime.fromisoformat('2026-10-25T02:15:00+01:00'))
    result = flow(flow_http, sample)
    occupied = [bucket for bucket in result['buckets'] if bucket['count']]
    assert len(occupied) == 2 and result['inWindow'] == 2
    assert occupied[0]['bucketStart'] == '2026-10-25T02:00:00+02:00'
    assert occupied[1]['bucketStart'] == '2026-10-25T02:00:00+01:00'


def test_manual_entry_without_timestamp_is_not_invented_and_undo_removes_presence(flow_http, sample):
    configure(sample)
    ref = participant(sample, 'manual', entered=True)
    result = flow(flow_http, sample)
    assert result['totalEntered'] == 1 and result['missingTimestamp'] == 1 and result['inWindow'] == 0
    ParticipantsService().update(sample.event.id, ref.id, ParticipantUpdateRequestDTO(
        event_id=sample.event.id, participant_id=ref.id, entered=False))
    result = flow(flow_http, sample)
    assert result['totalEntered'] == 0 and result['missingTimestamp'] == 0
    assert EntranceService()._build_event_counts(sample.event.id)['entered_count'] == 0


def test_explicit_flow_overrides_remain_supported(flow_http, sample):
    configure(sample, start='20:00', end='06:00')
    result = flow(flow_http, sample, start_time='18:30', span_hours=1, bucket_minutes=15)
    assert result['windowStart'] == '2026-11-15T18:30:00+01:00'
    assert result['windowEnd'] == '2026-11-15T19:30:00+01:00'
    assert len(result['buckets']) == 4


def test_old_snapshot_is_explicitly_marked_for_rebuild_without_rewriting_it(flow_http, sample):
    configure(sample)
    ref = db.document('analytics_event/' + sample.event.id)
    old = {'event_id': sample.event.id, 'kpis': {'entered': 99},
           'charts': {'entrance_flow': [{'count': 99}]}}
    ref.set(old)
    result = flow_http.get('/snapshot', query_string={'event_id': sample.event.id})
    assert result.status_code == 200
    assert result.get_json()['exists'] is False and result.get_json()['rebuild_required'] is True
    assert ref.get().to_dict() == old


@pytest.mark.parametrize('timestamp', ['2026-11-15T20:30:00', 'not-a-timestamp', None])
def test_unknown_scan_time_stays_in_total_but_not_in_graph(flow_http, sample, timestamp):
    configure(sample)
    scan(sample, 'legacy', timestamp)
    result = flow(flow_http, sample)
    assert (result['totalEntered'], result['inWindow'], result['outsideWindow'], result['missingTimestamp']) == (1, 0, 0, 1)


def test_invalid_event_date_does_not_assign_entrances_to_today(flow_http, sample):
    configure(sample, date='not-a-date')
    participant(sample, 'manual', entered=True, timestamp=sample.now)
    result = flow(flow_http, sample)
    assert result['totalEntered'] == 1 and result['invalidWindow'] is True
    assert result['windowStart'] is None and result['windowEnd'] is None and result['buckets'] == []


def test_stale_manual_timestamp_without_presence_does_not_count(flow_http, sample):
    configure(sample)
    participant(sample, 'undone', entered=False, timestamp=sample.now)
    result = flow(flow_http, sample)
    assert result['totalEntered'] == 0 and result['anomalies']['stale_timestamp'] == 1
