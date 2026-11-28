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
    assert [change['path'] for change in changes] == ['events/past', 'events/past-no-status', 'events/tonight-still-running']
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
    assert [change['path'] for change in changes] == ['memberships/expired']
    assert changes[0]['old'] is True and changes[0]['new'] is False
    assert sorted(manual) == ['bad-index', 'missing-index', 'no-index']


def test_text_prices_become_numbers_and_odd_values_are_only_listed():
    docs = [('events/e/participants_event/a', dict(price='15')), ('events/e/participants_event/b', dict(price='0')),
            ('events/e/participants_event/c', dict(price='12.50')), ('events/e/participants_event/d', dict(price='gratis')),
            ('events/e/participants_event/e', dict(price=15.0)), ('events/e/participants_event/f', dict(price=None))]
    changes, manual = reconcile.plan_participant_prices(docs)
    assert [(c['path'][-1], c['old'], c['new']) for c in changes] == [('a', '15', 15.0), ('b', '0', 0.0), ('c', '12.50', 12.5)]
    assert manual == ['events/e/participants_event/d']


def test_only_ids_of_deleted_memberships_are_removed_from_purchases():
    purchases = [('p1', dict(membership_ids=['gone', 'alive'])), ('p2', dict(membership_ids=['alive'])),
                 ('p3', dict(membership_ids=[])), ('p4', dict())]
    changes = reconcile.plan_purchase_memberships(purchases, {'alive'})
    assert changes == [dict(category='purchase_memberships', path='purchases/p1', field='membership_ids',
                            old=['gone', 'alive'], new=['alive'])]


def test_review_items_list_ids_only_and_never_become_changes():
    members = [('m1', dict(email='a@x.it', phone='+39 333 111')), ('m2', dict(email='', phone='0039333111')),
               ('m3', dict(email='c@x.it', phone='+39 333 111')), ('m4', dict(email='d@x.it'))]
    parts = [('p', dict(discountCodeId='c1')), ('q', dict(discountCodeId='c1')), ('r', dict())]
    codes = [('c1', dict(usedCount=2)), ('c2', dict(usedCount=1)), ('c3', dict(usedCount=0))]
    review = reconcile.review_items(members, parts, codes)
    assert review['memberships_without_email'] == ['m2']
    assert review['memberships_sharing_a_phone'] == [['m1', 'm3']]
    assert review['discount_codes_with_inconsistent_counter'] == ['c2']


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

    def document(self, path):
        return _Reference(self.store, path)

    def write_option(self, last_update_time):
        return ('precondition', last_update_time)


def _plan():
    return dict(changes=[
        dict(category='events_status', path='events/e1', field='status', old='active', new='ended'),
        dict(category='memberships_validity', path='memberships/m1', field='subscription_valid', old=True, new=False),
        dict(category='participant_prices', path='events/e1/participants_event/x', field='price', old='15', new=15.0)])


def test_apply_changes_one_field_after_writing_the_rollback_file(tmp_path):
    store = {'events/e1': dict(status='active', title='x'), 'memberships/m1': dict(subscription_valid=True, name='n'),
             'events/e1/participants_event/x': dict(price='15', name='z')}
    rollback = tmp_path / 'rollback.json'
    assert reconcile.apply_plan(_Client(store), _plan(), rollback) == 3
    assert store['events/e1'] == dict(status='ended', title='x')
    assert store['memberships/m1'] == dict(subscription_valid=False, name='n')
    assert store['events/e1/participants_event/x'] == dict(price=15.0, name='z')
    assert '"old": "active"' in rollback.read_text()


def test_apply_stops_before_any_write_if_a_document_changed_since_the_plan(tmp_path):
    store = {'events/e1': dict(status='active'), 'memberships/m1': dict(subscription_valid=False),
             'events/e1/participants_event/x': dict(price='15')}
    with pytest.raises(SystemExit, match='changed since the plan'):
        reconcile.apply_plan(_Client(store), _plan(), tmp_path / 'rollback.json')
    assert store['events/e1'] == dict(status='active') and not (tmp_path / 'rollback.json').exists()


def test_only_the_selected_categories_are_applied():
    chosen = reconcile.selected(_plan(), {'events_status', 'participant_prices'})
    assert [change['category'] for change in chosen] == ['events_status', 'participant_prices']
    assert reconcile.selected(_plan(), set()) == []
