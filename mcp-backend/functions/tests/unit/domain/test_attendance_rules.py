from datetime import datetime, timezone
from types import SimpleNamespace as NS

from domain.attendance_rules import (
    attendance_timestamp, build_entrance_flow, entrance_window, summarize_attendance,
)


def event(date, start='22:00', end=None):
    return NS(date=date, start_time=start, end_time=end)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_default_window_is_eight_real_hours_on_normal_night():
    start, end = entrance_window(event('2026-11-15'))
    assert (end - start).total_seconds() == 8 * 3600


def test_spring_forward_default_window_is_valid_and_real_eight_hours():
    # 28/03/2026 02:00 -> 03:00; start 18:30 + 8h would land on non-existent 02:30.
    start, end = entrance_window(event('2026-03-28', start='18:30'))
    assert (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds() == 8 * 3600


def test_spring_forward_span_is_real_elapsed_time():
    start, end = entrance_window(event('2026-03-28'), span_hours=6)
    assert (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds() == 6 * 3600


def test_fall_back_default_window_is_real_eight_hours():
    start, end = entrance_window(event('2026-10-24'))
    assert (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds() == 8 * 3600


def test_nonexistent_event_end_time_is_rejected():
    assert entrance_window(event('2026-03-28', start='22:00', end='02:30')) is None


def test_end_before_start_crosses_midnight():
    start, end = entrance_window(event('2026-11-15', start='22:00', end='04:00'))
    assert (end - start).total_seconds() == 6 * 3600


def test_timestamp_formats():
    assert attendance_timestamp('2026-11-15T20:30:00Z') == utc(2026, 11, 15, 20, 30)
    assert attendance_timestamp(1_794_000_000_000) == attendance_timestamp(1_794_000_000)
    assert attendance_timestamp('2026-11-15T20:30:00') is None  # naive
    assert attendance_timestamp(True) is None
    assert attendance_timestamp('garbage') is None
    assert attendance_timestamp(None) is None


def test_scan_is_only_proof_for_linked_members():
    people = [NS(id='p1', membership_id='m1', entered=True, entered_at=None),
              NS(id='p2', membership_id='m2', entered=True, entered_at=None),
              NS(id='p3', membership_id=None, entered=True, entered_at='2026-11-15T21:30:00+00:00')]
    scans = [NS(id='m1', scanned_at='2026-11-15T21:00:00+00:00')]
    a = summarize_attendance(people, scans)
    assert (a.registered, a.total_scanned, a.manual_entered, a.total_entered) == (3, 1, 1, 2)
    assert a.anomalies['missing_scan'] == 1  # m2 flagged, no scan: not counted


def test_orphan_scan_and_flag_mismatch_are_reported_not_hidden():
    people = [NS(id='p1', membership_id='m1', entered=False, entered_at=None)]
    scans = [NS(id='m1', scanned_at=None), NS(id='old', scanned_at=None)]
    a = summarize_attendance(people, scans)
    assert a.anomalies['flag_mismatch'] == 1 and a.anomalies['orphan_scan'] == 1
    assert a.total_entered == 2 and a.summary()['missing_timestamp'] == 2


def test_scan_without_id_does_not_collapse_with_others():
    a = summarize_attendance([], [NS(id=None, scanned_at=None), NS(id=None, scanned_at=None)])
    assert a.total_scanned == 2


def test_flow_total_independent_of_window_and_bounds():
    ev = event('2026-11-15', start='22:00', end='23:00')  # 21:00-22:00 UTC
    scans = [NS(id=f'm{i}', scanned_at=t) for i, t in enumerate([
        '2026-11-15T21:00:00+00:00',   # start: in
        '2026-11-15T21:59:59+00:00',   # in
        '2026-11-15T22:00:00+00:00',   # end: out
        '2026-11-15T10:00:00+00:00'])]  # out
    flow = build_entrance_flow(ev, summarize_attendance([], scans))
    assert flow['total_entered'] == 4 and flow['in_window'] == 2 and flow['outside_window'] == 2
    assert sum(b['count'] for b in flow['buckets']) == 2


def test_last_partial_bucket_is_clamped():
    ev = event('2026-11-15', start='22:00', end='22:45')
    flow = build_entrance_flow(ev, summarize_attendance([], []))
    assert len(flow['buckets']) == 2
    assert flow['buckets'][-1]['label'].endswith('22:45')


def test_fall_back_buckets_are_unique_instants():
    ev = event('2026-10-24', start='23:00')
    flow = build_entrance_flow(ev, summarize_attendance([], []))
    keys = [b['bucket_start'] for b in flow['buckets']]
    assert len(set(keys)) == len(keys)
