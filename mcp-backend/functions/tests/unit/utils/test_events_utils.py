from datetime import datetime

import pytest

from domain.event_rules import EVENT_TIMEZONE, get_event_end_datetime, is_event_finished
from models import Event
from utils.events_utils import ensure_event_is_active, validate_email_format


def test_validate_email_format_accepts_valid_email():
    assert validate_email_format("mario.rossi+test@gmail.com") is True


def test_validate_email_format_rejects_invalid_email():
    assert validate_email_format("mario.rossi.gmail.com") is False
    assert validate_email_format("mario@localhost") is False
    assert validate_email_format("mario@") is False


def test_event_end_datetime_handles_overnight_event():
    event = Event(date="21-02-2026", start_time="23:00", end_time="05:00")

    end_dt = get_event_end_datetime(event)

    assert end_dt == datetime(2026, 2, 22, 5, 0, tzinfo=EVENT_TIMEZONE)


def test_event_end_datetime_falls_back_to_twelve_hours_for_till_late():
    event = Event(date="21-02-2026", start_time="23:00", end_time="Till late")

    end_dt = get_event_end_datetime(event)

    assert end_dt == datetime(2026, 2, 22, 11, 0, tzinfo=EVENT_TIMEZONE)


def test_is_event_finished_uses_computed_end_time():
    event = Event(date="21-02-2026", start_time="23:00", end_time="05:00")

    assert is_event_finished(event, now=datetime(2026, 2, 22, 4, 59, tzinfo=EVENT_TIMEZONE)) is False
    assert is_event_finished(event, now=datetime(2026, 2, 22, 5, 0, tzinfo=EVENT_TIMEZONE)) is True


def test_ensure_event_is_active_blocks_finished_event():
    event = Event(date="21-02-2026", start_time="23:00", end_time="05:00")

    with pytest.raises(ValueError):
        ensure_event_is_active(event)
