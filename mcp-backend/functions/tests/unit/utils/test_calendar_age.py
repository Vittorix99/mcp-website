"""Q-06: admission and age bands use completed calendar years in Rome."""
import datetime as dates
from zoneinfo import ZoneInfo

import pytest

from services.core import analytics_service, analytics_snapshot_service
from utils import events_utils

REAL_DATE = dates.date
REAL_DATETIME = dates.datetime


def freeze_clock(monkeypatch, instant):
    class Clock(REAL_DATETIME):
        @classmethod
        def now(cls, tz=None):
            assert tz == ZoneInfo('Europe/Rome')
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    class HostDate(REAL_DATE):
        @classmethod
        def today(cls):
            return instant.date()

    monkeypatch.setattr(events_utils.datetime, 'datetime', Clock)
    monkeypatch.setattr(events_utils.datetime, 'date', HostDate)
    monkeypatch.setattr(analytics_service, 'datetime', Clock)
    monkeypatch.setattr(analytics_snapshot_service, 'datetime', Clock)


@pytest.mark.parametrize('today,birth,minor,under21,age', [
    ('2026-11-15','16-11-2008',True,True,17),
    ('2026-11-15','15-11-2008',False,True,18),
    ('2026-11-15','14-11-2008',False,True,18),
    ('2026-11-15','16-11-2005',False,True,20),
    ('2026-11-15','15-11-2005',False,False,21),
    ('2026-11-15','14-11-2005',False,False,21),
    ('2026-02-28','29-02-2008',True,True,17),
    ('2026-03-01','29-02-2008',False,True,18),
    ('2029-02-28','29-02-2008',False,True,20),
    ('2029-03-01','29-02-2008',False,False,21),
    ('2028-02-28','29-02-2008',False,True,19),
    ('2028-02-29','29-02-2008',False,True,20),
])
def test_calendar_boundaries_match_admission_and_both_analytics(monkeypatch, today, birth, minor, under21, age):
    instant = REAL_DATETIME.fromisoformat(today+'T12:00:00+00:00')
    freeze_clock(monkeypatch, instant)
    assert events_utils.is_minor(birth) is minor
    assert events_utils.is_Under_21(birth) is under21
    assert analytics_service.AnalyticsService.__new__(analytics_service.AnalyticsService)._age_from_birthdate(birth) == age
    assert analytics_snapshot_service.AnalyticsSnapshotService.__new__(analytics_snapshot_service.AnalyticsSnapshotService)._age_from_birthdate(birth) == age


def test_rome_birthday_can_precede_the_utc_calendar_date(monkeypatch):
    freeze_clock(monkeypatch, REAL_DATETIME(2026,11,14,23,30,tzinfo=dates.timezone.utc))
    assert events_utils.is_minor('15-11-2008') is False
    assert events_utils.is_Under_21('15-11-2005') is False


@pytest.mark.parametrize('birth', [None,'','not-a-date','31-02-2000','15-11-2100'])
def test_invalid_or_future_birthdates_cannot_pass_admission(monkeypatch, birth):
    freeze_clock(monkeypatch, REAL_DATETIME(2026,11,15,12,tzinfo=dates.timezone.utc))
    assert events_utils.is_minor(birth) is True
    assert events_utils.is_Under_21(birth) is True
