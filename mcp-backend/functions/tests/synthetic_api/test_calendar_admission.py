"""Q-06 admission boundaries through checkout handlers and the real Firestore emulator."""
import datetime as dates
from types import SimpleNamespace

import pytest

from config.firebase_config import db
from utils import events_utils

REAL_DATETIME = dates.datetime


@pytest.mark.parametrize('instant,birth,over21,expected', [
    ('2026-11-15T12:00:00+00:00','16-11-2008',False,400),
    ('2026-11-15T12:00:00+00:00','15-11-2008',False,201),
    ('2026-11-15T12:00:00+00:00','16-11-2005',True,400),
    ('2026-11-15T12:00:00+00:00','15-11-2005',True,201),
    ('2026-02-28T12:00:00+00:00','29-02-2008',False,400),
    ('2026-03-01T12:00:00+00:00','29-02-2008',False,201),
    ('2026-11-14T23:30:00+00:00','15-11-2008',False,201),
])
def test_checkout_uses_rome_calendar_age_before_calling_the_provider(http, sample, gateway, monkeypatch, instant, birth, over21, expected):
    moment = REAL_DATETIME.fromisoformat(instant)
    class Clock(REAL_DATETIME):
        @classmethod
        def now(cls, tz=None):
            return moment.astimezone(tz) if tz else moment.replace(tzinfo=None)
    # Replace this module's clock, never datetime globally or the Firestore SDK clock.
    monkeypatch.setattr(events_utils, 'datetime', SimpleNamespace(**{**vars(dates),'datetime':Clock}))
    sample.event.over21_only = over21
    db.document('events/' + sample.event.id).set(sample.event.to_firestore())
    before_members = {row.id:row.to_dict() for row in db.collection('memberships').stream()}
    response = http.post('/orders',json={'cart':[{'eventId':sample.event.id,'participants':[
        {'name':person.name,'surname':person.surname,'email':person.email,'phone':person.phone,'birthdate':birth}
        for person in sample.people]}]})
    assert response.status_code == expected, response.get_json()
    assert gateway.create_calls == (1 if expected == 201 else 0)
    assert not list(db.collection('purchases').stream())
    assert not list(db.collection(f'participants/{sample.event.id}/participants_event').stream())
    assert {row.id:row.to_dict() for row in db.collection('memberships').stream()} == before_members
    if expected == 400:
        assert not list(db.collection('orders').stream())
