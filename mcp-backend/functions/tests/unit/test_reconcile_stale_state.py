import importlib.util
from datetime import datetime
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/database_bug_fix/reconcile_stale_state.py'
spec = importlib.util.spec_from_file_location('reconcile_stale_state', SCRIPT)
reconcile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconcile)
ZONE = reconcile.EVENT_TIMEZONE
NOW = datetime(2026, 11, 29, 12, 0, tzinfo=ZONE)


def test_only_finished_active_events_are_ended():
    docs = [('past', dict(status='active', date='28-06-2026', startTime='22:00', endTime='04:00')),
            ('past-no-status', dict(date='01-11-2026', startTime='21:00')),
            ('future', dict(status='active', date='30-11-2026', startTime='22:00')),
            ('tonight-still-running', dict(status='active', date='28-11-2026', startTime='23:00', endTime='06:00')),
            ('already-ended', dict(status='ended', date='01-01-2026')),
            ('sold-out-past', dict(status='sold_out', date='01-01-2026')),
            ('coming-soon', dict(status='coming_soon', date='02-01-2026')),
            ('undated', dict(status='active'))]
    changes = reconcile.plan_events(docs, NOW)
    assert [change['id'] for change in changes] == ['past', 'past-no-status', 'tonight-still-running']
    assert all(change['field'] == 'status' and change['old'] == 'active' and change['new'] == 'ended' for change in changes)


def test_event_ending_after_midnight_is_not_closed_early():
    docs = [('night', dict(status='active', date='28-11-2026', startTime='23:00', endTime='06:00'))]
    assert reconcile.plan_events(docs, datetime(2026, 11, 29, 3, 0, tzinfo=ZONE)) == []
    assert len(reconcile.plan_events(docs, datetime(2026, 11, 29, 6, 1, tzinfo=ZONE))) == 1


def test_memberships_are_invalidated_only_with_a_reliable_year_index():
    docs = [('expired', dict(subscription_valid=True, membership_years=[2024, 2025])),
            ('current', dict(subscription_valid=True, membership_years=[2025, 2026])),
            ('already-invalid', dict(subscription_valid=False, membership_years=[2024])),
            ('no-index', dict(subscription_valid=True, membership_years=[])),
            ('missing-index', dict(subscription_valid=True)),
            ('bad-index', dict(subscription_valid=True, membership_years=['2026'])),
            ('truthy-not-true', dict(subscription_valid='yes', membership_years=[2020]))]
    changes, manual = reconcile.plan_memberships(docs, 2026)
    assert [change['id'] for change in changes] == ['expired']
    assert changes[0]['old'] is True and changes[0]['new'] is False
    assert sorted(manual) == ['bad-index', 'missing-index', 'no-index']


class _Snapshot:
    def __init__(self, data):
        self.data, self.exists, self.update_time = data, True, 'T1'

    def to_dict(self):
        return self.data


class _Reference:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def get(self):
        return _Snapshot(self.store[self.key])

    def update(self, values, option=None):
        assert option == ('precondition', 'T1')
        self.store[self.key].update(values)


class _Client:
    def __init__(self, store):
        self.store = store

    def collection(self, name):
        client = self
        return type('C', (), {'document': lambda _, doc_id: _Reference(client.store, (name, doc_id))})()

    def write_option(self, last_update_time):
        return ('precondition', last_update_time)


def test_apply_changes_one_field_after_writing_the_rollback_file(tmp_path):
    store = {('events', 'e1'): dict(status='active', title='x'), ('memberships', 'm1'): dict(subscription_valid=True, name='n')}
    plan = dict(changes=[dict(collection='events', id='e1', field='status', old='active', new='ended'),
                         dict(collection='memberships', id='m1', field='subscription_valid', old=True, new=False)])
    rollback = tmp_path / 'rollback.json'
    assert reconcile.apply_plan(_Client(store), plan, rollback) == 2
    assert store[('events', 'e1')] == dict(status='ended', title='x')
    assert store[('memberships', 'm1')] == dict(subscription_valid=False, name='n')
    assert '"old": "active"' in rollback.read_text()


def test_apply_stops_before_any_write_if_a_document_changed_since_the_plan(tmp_path):
    store = {('events', 'e1'): dict(status='active'), ('memberships', 'm1'): dict(subscription_valid=False)}
    plan = dict(changes=[dict(collection='events', id='e1', field='status', old='active', new='ended'),
                         dict(collection='memberships', id='m1', field='subscription_valid', old=True, new=False)])
    with pytest.raises(SystemExit, match='changed since the plan'):
        reconcile.apply_plan(_Client(store), plan, tmp_path / 'rollback.json')
    assert store[('events', 'e1')] == dict(status='active') and not (tmp_path / 'rollback.json').exists()
