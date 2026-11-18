"""Checks fixture integrity without Firebase, credentials, or network access."""
import importlib.util
import json
from datetime import date
from pathlib import Path
from collections import Counter

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('synthetic_generator', ROOT / 'scripts/staging/generate.py')
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def build(**kwargs):
    return generator.generate(seed=42, as_of=date(2026, 11, 7), email_base='owner@example.com', **kwargs)


def test_full_dataset_has_exact_counts_and_every_member_participates():
    data = build()
    rows = {r['path']: r['data'] for r in data['records']}
    assert len(rows) == len(data['records'])
    members = {p: d for p, d in rows.items() if p.startswith('memberships/')}
    events = {p: d for p, d in rows.items() if p.startswith('events/')}
    assert len(members) == 4000
    birth_years = {int(member['birthdate'][-4:]) for member in members.values()}
    assert birth_years == set(range(1985, 2009))
    assert len(events) == 50
    participation = Counter()
    for path, participant in rows.items():
        if not path.startswith('participants/'):
            continue
        member_id = participant['membershipId']
        participation[member_id] += 1
        assert f'memberships/{member_id}' in members
        assert participant['birthdate'] == members[f'memberships/{member_id}']['birthdate']
        assert f"events/{participant['event_id']}" in events
        if participant.get('purchase_id'):
            assert f"purchases/{participant['purchase_id']}" in rows
        assert participant['send_ticket_on_create'] is False
    assert set(participation) == {p.split('/')[1] for p in members}
    assert min(participation.values()) >= 1
    assert max(participation.values()) > 1
    assert len({m['email'] for m in members.values()}) == 4000
    assert {e['status'] for e in events.values()} == {'ended', 'active', 'sold_out', 'coming_soon'}
    assert {e['type'] for e in events.values()} == {'PUBLIC', 'ONLY_ALREADY_REGISTERED_MEMBERS', 'ONLY_MEMBERS', 'ON_REQUEST'}
    assert any(not m['subscription_valid'] and 2026 not in m['membership_years'] for m in members.values())
    assert any(not m['subscription_valid'] and 2026 in m['membership_years'] for m in members.values())


def test_same_seed_reproduces_bytes_and_other_seed_changes_assignments():
    settings = dict(member_count=30, event_count=12)
    first = build(**settings)
    assert generator.encode(first) == generator.encode(build(**settings))
    other = generator.generate(seed=43, as_of=date(2026, 11, 7), email_base='owner@example.com', **settings)
    assert generator.encode(first) != generator.encode(other)


def test_purchase_ledger_matches_independent_integer_sums_and_groups():
    data = build(member_count=120, event_count=16)
    rows = {r['path']: r['data'] for r in data['records']}
    totals = Counter()
    from decimal import Decimal
    for path, purchase in rows.items():
        if not path.startswith('purchases/'):
            continue
        assert purchase['status'] == purchase['capture_status'] == 'COMPLETED'
        order = rows['orders/' + purchase['order_id']]
        assert order['purchase_id'] == path.split('/')[1]
        assert order['captured'] is True
        participants = [p for key, p in rows.items() if key.startswith('participants/') and p.get('purchase_id') == path.split('/')[1]]
        assert len(participants) == purchase['participants_count']
        gross = int(Decimal(purchase['amount_total']) * 100)
        net = int(Decimal(purchase['net_amount']) * 100)
        fee = int(Decimal(purchase['paypal_fee']) * 100)
        assert gross == net + fee
        totals['gross_cents'] += gross
        totals['net_cents'] += net
        totals['fee_cents'] += fee
        totals['paid_tickets'] += len(participants)
        totals['purchases'] += 1
    expected = data['manifest']['expected']['global']
    for key, value in totals.items():
        assert expected[key] == value
    assert totals['paid_tickets'] > totals['purchases']


def test_scans_are_unique_and_match_flags_and_are_not_live_scanner_tokens():
    data = build(member_count=100, event_count=16)
    rows = {r['path']: r['data'] for r in data['records']}
    scans = {p: d for p, d in rows.items() if p.startswith('entrance_scans/')}
    entered = 0
    for path, d in rows.items():
        if path.startswith('scan_tokens/'):
            assert d['is_active'] is False
        if path.startswith('participants/'):
            scan_path = f"entrance_scans/{d['event_id']}/scans/{d['membershipId']}"
            assert d['entered'] == (scan_path in scans)
            entered += d['entered']
        if path.startswith('memberships/'):
            assert d['send_card_on_create'] is False
            assert not d.get('wallet_pass_id')
    assert 0 < entered == len(scans) < data['manifest']['expected']['global']['participants']
    assert any(d['manual'] for d in scans.values())
    assert any(not d['manual'] for d in scans.values())


def test_bad_purchase_states_are_isolated_and_delta_is_not_a_fake_payment():
    data = build(member_count=30, event_count=12)
    variants = data['isolated_cases']
    states = {'FAILED', 'CANCELLED', 'VOIDED', 'REFUNDED', 'DECLINED', 'ERROR'}
    assert states <= {v['state'] for v in variants if v.get('field') == 'status'}
    assert states <= {v['state'] for v in variants if v.get('field') == 'capture_status'}
    baseline = {r['path']: r['data'] for r in data['records']}
    for variant in variants:
        if variant.get('field') not in {'status', 'capture_status'}:
            continue
        replacement = variant['replace'][0]
        original = baseline[replacement['path']]
        assert original['status'] == original['capture_status'] == 'COMPLETED'
        assert replacement['data'][variant['field']] == variant['state']
        assert variant['expected_delta']['event_gross_cents'] < 0
        assert variant['execution'] == 'not_run'
    assert all(v['status'] == 'not_run' for v in data['manifest']['api_cases'])


@pytest.mark.parametrize('changes', [dict(member_count=0), dict(event_count=3), dict(email_base='not-an-email')])
def test_invalid_configuration_is_rejected(changes):
    kwargs = dict(seed=42, as_of=date(2026, 11, 7), email_base='owner@example.com', member_count=30, event_count=12)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        generator.generate(**kwargs)


def test_generation_is_offline(monkeypatch):
    import socket
    def deny(*args, **kwargs):
        raise AssertionError('Generator must not access the network')
    monkeypatch.setattr(socket, 'socket', deny)
    build(member_count=30, event_count=12)


def test_zero_price_participants_are_omaggi_and_future_events_have_no_scans():
    data = build(member_count=100, event_count=16)
    rows = {r['path']: r['data'] for r in data['records']}
    for path, row in rows.items():
        if path.startswith('participants/'):
            event = rows['events/' + row['event_id']]
            if row['price'] == 0:
                assert row['payment_method'] == 'omaggio'
            if event['status'] != 'ended':
                assert row['entered'] is False


def test_private_export_rejects_public_path_and_roundtrips_timestamps(tmp_path, monkeypatch):
    data = build(member_count=30, event_count=12)
    monkeypatch.setattr(generator, 'ROOT', tmp_path)
    with pytest.raises(ValueError):
        generator.write_export(data, tmp_path / 'public')
    output = tmp_path / '.local/staging/dataset'
    generator.write_export(data, output)
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['members'] == 30
    assert (output / 'records.jsonl').stat().st_mode & 0o777 == 0o600
    assert output.stat().st_mode & 0o777 == 0o700
    first = (output / 'records.jsonl').read_bytes()
    generator.write_export(data, output)
    assert (output / 'records.jsonl').read_bytes() == first


def test_expired_members_have_only_historical_participations_covered_by_their_years():
    data = build(member_count=100, event_count=16)
    rows = {r['path']: r['data'] for r in data['records']}
    for row in data['records']:
        if row['path'].startswith('participants/'):
            participant = row['data']
            member = rows['memberships/' + participant['membershipId']]
            if member['end_date'].endswith('2025'):
                event = rows['events/' + participant['event_id']]
                assert int(event['date'][-4:]) in member['membership_years']


def test_historical_tokens_exist_only_for_past_events_and_last_twelve_hours():
    from datetime import datetime, timedelta, timezone
    data = build(member_count=30, event_count=12)
    rows = {r['path']: r['data'] for r in data['records']}
    for path, token in rows.items():
        if not path.startswith('scan_tokens/'):
            continue
        assert rows['events/' + token['event_id']]['status'] == 'ended'
        assert token['created_at'] < datetime(2026, 11, 7, tzinfo=timezone.utc)
        assert token['expires_at'] - token['created_at'] == timedelta(hours=12)
