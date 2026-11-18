"""Attendance facts and dated event charts, without writing or repairing history."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from math import ceil
from zoneinfo import ZoneInfo

from domain.event_rules import parse_event_date, parse_event_time

ROME = ZoneInfo('Europe/Rome')
ATTENDANCE_VERSION = 1


def attendance_timestamp(value):
    if hasattr(value, 'to_datetime') and callable(value.to_datetime):
        try:
            value = value.to_datetime()
        except Exception:
            return None
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = datetime.fromtimestamp(value / 1000 if value > 1e12 else value, timezone.utc)
        elif isinstance(value, str):
            value = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except (ValueError, TypeError, OverflowError, OSError):
        return None
    # A legacy value without a zone does not prove the instant of an entrance.
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        return None
    return value.astimezone(timezone.utc)


@dataclass
class Attendance:
    registered: int
    entered_flag: int
    total_scanned: int
    manual_entered: int
    timestamps: list
    anomalies: dict

    @property
    def total_entered(self):
        return len(self.timestamps)

    def summary(self):
        return {'registered': self.registered, 'entered_flag': self.entered_flag,
                'total_scanned': self.total_scanned, 'manual_entered': self.manual_entered,
                'total_entered': self.total_entered,
                'missing_timestamp': sum(value is None for value in self.timestamps),
                'anomalies': self.anomalies}


def summarize_attendance(participants, scans):
    participants, scans = list(participants), list(scans)
    scan_by_member = {getattr(scan, 'id', None) or ('unknown_scan', index): scan
                      for index, scan in enumerate(scans)}
    linked, registered, manual_times, stale_times = {}, set(), [], 0
    for index, person in enumerate(participants):
        member_id = getattr(person, 'membership_id', None)
        registered.add(('member', member_id) if member_id else
                       ('participant', getattr(person, 'id', None) or index))
        entered = bool(getattr(person, 'entered', False))
        timestamp = getattr(person, 'entered_at', None)
        if member_id:
            linked.setdefault(member_id, []).append(person)
        elif entered:
            manual_times.append(attendance_timestamp(timestamp))
        if not entered and timestamp is not None:
            stale_times += 1
    anomalies = {
        'missing_scan': sum(member_id not in scan_by_member and any(bool(getattr(p, 'entered', False)) for p in rows)
                            for member_id, rows in linked.items()),
        'flag_mismatch': sum(member_id in scan_by_member and any(not bool(getattr(p, 'entered', False)) for p in rows)
                             for member_id, rows in linked.items()),
        'orphan_scan': sum(member_id not in linked for member_id in scan_by_member),
        'stale_timestamp': stale_times,
    }
    timestamps = [attendance_timestamp(getattr(scan, 'scanned_at', None)) for scan in scan_by_member.values()]
    return Attendance(len(registered), sum(bool(getattr(p, 'entered', False)) for p in participants),
                      len(scan_by_member), len(manual_times), timestamps + manual_times, anomalies)


def _after(start, delta):
    # Elapsed time, not wall-clock arithmetic: stays correct across DST changes.
    return (start.astimezone(timezone.utc) + delta).astimezone(ROME)


def entrance_window(event, start_time=None, span_hours=None):
    event_date = parse_event_date(getattr(event, 'date', None))
    if event_date is None:
        try:
            event_date = date.fromisoformat(str(getattr(event, 'date', '')))
        except ValueError:
            return None
    clock = parse_event_time(start_time) or parse_event_time(getattr(event, 'start_time', None)) or time(22)
    start = datetime.combine(event_date, clock, tzinfo=ROME)
    end_clock = parse_event_time(getattr(event, 'end_time', None))
    computed_end = True
    if span_hours is not None:
        end = _after(start, timedelta(hours=max(1, min(24, int(span_hours)))))
    elif end_clock is None:
        end = _after(start, timedelta(hours=8))
    else:
        computed_end = False
        end = datetime.combine(event_date, end_clock, tzinfo=ROME)
        if end <= start:
            end += timedelta(days=1)
    # Reject non-existent local clock times taken from event data. Computed ends are
    # real elapsed time, so they are always valid instants.
    checked = (start,) if computed_end else (start, end)
    if any(value.astimezone(timezone.utc).astimezone(ROME).replace(tzinfo=None) != value.replace(tzinfo=None)
           for value in checked):
        return None
    return start, end


def build_entrance_flow(event, attendance, *, start_time=None, span_hours=None, bucket_minutes=30):
    window = entrance_window(event, start_time, span_hours)
    summary = {**attendance.summary(), 'in_window': 0, 'outside_window': 0,
               'window_start': None, 'window_end': None, 'invalid_window': window is None}
    if window is None:
        return {**summary, 'buckets': []}
    local_start, local_end = window
    start, end = local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)
    minutes = bucket_minutes if bucket_minutes in {5, 10, 15, 30, 60} else 30
    step = timedelta(minutes=minutes)
    counts = [0] * ceil((end - start).total_seconds() / step.total_seconds())
    for timestamp in attendance.timestamps:
        if timestamp is None:
            continue
        if start <= timestamp < end:
            counts[int((timestamp - start).total_seconds() // step.total_seconds())] += 1
        else:
            summary['outside_window'] += 1
    cumulative, buckets = 0, []
    for index, count in enumerate(counts):
        bucket_start = (start + index * step).astimezone(ROME)
        bucket_end = min(start + (index + 1) * step, end).astimezone(ROME)
        cumulative += count
        buckets.append({'bucket_start': bucket_start.isoformat(), 'bucket_end': bucket_end.isoformat(),
                        'hour_label': bucket_start.strftime('%H:%M'),
                        'label': f'{bucket_start:%H:%M} - {bucket_end:%H:%M}',
                        'count': count, 'cumulative': cumulative})
    return {**summary, 'in_window': cumulative, 'window_start': local_start.isoformat(),
            'window_end': local_end.isoformat(), 'buckets': buckets}
