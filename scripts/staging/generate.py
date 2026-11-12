#!/usr/bin/env python3
"""Deterministic synthetic data export. Never connects to Firebase or providers."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'mcp-backend/functions'))
from models import (  # noqa: E402
    EntranceScan, Event, EventOrder, EventParticipant, EventPurchase,
    EventPurchaseAccessType, EventStatus, Membership, PaymentMethod,
    PurchaseStatus,
)
from models.scan_token import ScanToken  # noqa: E402

ROME = ZoneInfo('Europe/Rome')
MALE_NAMES = ('Marco', 'Luca', 'Paolo', 'Matteo', 'Davide', 'Stefano')
FEMALE_NAMES = ('Giulia', 'Sara', 'Elena', 'Chiara', 'Alice', 'Francesca')
SURNAMES = ('Rossi', 'Bianchi', 'Verdi', 'Moretti', 'Galli', 'Costa', 'Fontana', 'Marini')
MONEY_KEYS = ('purchases', 'paid_tickets', 'gross_cents', 'net_cents', 'fee_cents')


def money(cents):
    return str((Decimal(cents) / 100).quantize(Decimal('0.01')))


def encode(value):
    """Timestamp tags retain Firestore types without storing personal values in logs."""
    def timestamp(item):
        if isinstance(item, datetime):
            return {'$timestamp': item.isoformat()}
        raise TypeError(f'Unsupported export type: {type(item).__name__}')
    return json.dumps(value, default=timestamp, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def _counter():
    return Counter({key: 0 for key in (*MONEY_KEYS, 'participants', 'entered', 'manual_entries', 'omaggi')})


def generate(*, seed, as_of, email_base, member_count=4000, event_count=50):
    """Generate ordinary history plus isolated replacements; no service is invoked."""
    if not isinstance(as_of, date) or isinstance(as_of, datetime) or as_of.year < 2000:
        raise ValueError('as_of must be a date from year 2000 onward')
    if (not all(isinstance(value, int) for value in (seed, member_count, event_count))
            or not 20 <= member_count <= 10000 or not 12 <= event_count <= 100):
        raise ValueError('Use 20..10000 members, 12..100 events and an integer seed')
    if not isinstance(email_base, str) or not re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', email_base):
        raise ValueError('A valid controlled email base is required')
    local, domain = email_base.lower().split('@')
    if len(local + '+staging-user-10000') > 64 or '..' in local:
        raise ValueError('Email local part is too long or malformed')
    rng = random.Random(seed)
    records, members, events = [], {}, {}
    expected_events, cohorts = {}, Counter()
    expected = _counter()
    assignments = defaultdict(list)
    year = as_of.year
    past_count = event_count * 3 // 5
    modes = list(EventPurchaseAccessType)

    def add(path, model, scenarios):
        records.append({'path': path, 'data': model.to_firestore(), 'scenario_ids': scenarios})

    for i in range(event_count):
        event_id = f'syn-event-{i:03d}'
        historical = i < past_count
        if historical:
            event_date = date(year - 1, 11, 1) + timedelta(days=i) if i < 2 else as_of - timedelta(days=(i - 1) * 3)
            status = EventStatus.ENDED
        else:
            event_date = as_of + timedelta(days=i - past_count + 1)
            status = (EventStatus.ACTIVE, EventStatus.SOLD_OUT, EventStatus.COMING_SOON)[(i - past_count) % 3]
            if i == event_count - 1:
                status = EventStatus.COMING_SOON
        mode = modes[i % len(modes)]
        event = Event(
            id=event_id, title=f'Evento sintetico {i:03d}', slug=event_id,
            date=event_date.strftime('%d-%m-%Y'), start_time='22:00', end_time='06:00',
            location_hint='Luogo di prova', location_label='Spazio sintetico',
            price=0.0 if i % 11 == 5 else float(money(1500 + (i % 5) * 500)),
            fee=2.0, purchase_mode=mode, status=status,
            over21_only=i % 7 == 3, only_females=i % 9 == 4,
            allow_duplicates=i % 13 == 7, created_by='synthetic-seed',
            note='Dati inventati. Nessuna transazione o invio reale.',
        )
        events[event_id] = event
        expected_events[event_id] = _counter()

    for i in range(member_count):
        member_id = f'syn-member-{i:05d}'
        cohort = 'active' if i % 10 < 7 else ('expired' if i % 10 < 9 else 'invalidated')
        cohorts[cohort] += 1
        gender = 'female' if i % 2 == 0 else 'male'
        age = 20 if i % 17 == 0 else rng.randint(22, 68)
        birth = date(year - age, 1, 10)
        years = [year - 1] if cohort == 'expired' else [year - 1, year]
        renewals = [{'year': y, 'start_date': f'{y}-01-01T12:00:00+00:00',
                     'end_date': f'31-12-{y}', 'purchase_id': None, 'fee': 20.0} for y in years]
        membership = Membership(
            id=member_id, slug=member_id,
            name=rng.choice(FEMALE_NAMES if gender == 'female' else MALE_NAMES),
            surname=rng.choice(SURNAMES), email=f'{local}+staging-user-{i:05d}@{domain}',
            phone=f'+999000{i:07d}', birthdate=birth.strftime('%d-%m-%Y'),
            start_date=renewals[-1]['start_date'], end_date=renewals[-1]['end_date'],
            subscription_valid=cohort == 'active', membership_years=years,
            renewals=renewals, membership_fee=20.0, membership_type='manual',
            send_card_on_create=False, newsletter_consent=i % 3 == 0,
        )
        members[member_id] = membership
        eligible = []
        for event_id, event in events.items():
            event_year = datetime.strptime(event.date, '%d-%m-%Y').year
            if event.status != EventStatus.ENDED:
                continue
            if cohort == 'expired' and event_year not in years:
                continue
            if event.over21_only and age - (year - event_year) < 21:
                continue
            if event.only_females and gender != 'female':
                continue
            if event.purchase_mode != EventPurchaseAccessType.PUBLIC and event_year not in years:
                continue
            eligible.append(event_id)
        # Event zero is unrestricted, historical, and covered by every member's history.
        selected = {'syn-event-000'}
        count = len(eligible) if i % 97 == 0 else rng.randint(1, min(8, len(eligible)))
        selected.update(rng.sample(eligible, count))
        for event_id in sorted(selected):
            assignments[event_id].append((member_id, gender))

    # Reserve an empty upcoming event; populate active/sold-out ones with valid members only.
    for index, (event_id, event) in enumerate(events.items()):
        if index < past_count or index == event_count - 1 or event.status == EventStatus.COMING_SOON:
            continue
        candidates = [(mid, 'female' if n % 2 == 0 else 'male') for n, (mid, m) in enumerate(members.items())
                      if m.subscription_valid and (not event.only_females or n % 2 == 0)
                      and (not event.over21_only or year - int(m.birthdate[-4:]) >= 21)]
        rng.shuffle(candidates)
        assignments[event_id] = candidates[:max(1, member_count // 20)]

    purchase_index = 0
    for index, (event_id, event) in enumerate(events.items()):
        people = assignments[event_id]
        event_day = datetime.strptime(event.date, '%d-%m-%Y').date()
        event_start = datetime.combine(event_day, time(22), ROME)
        historical = event.status == EventStatus.ENDED
        creation = min(event_start - timedelta(days=3), datetime.combine(as_of, time(10), ROME))
        ledger = expected_events[event_id]
        historical_token = f'syn-history-scanner-{index:03d}'
        if historical:
            token_created = (event_start - timedelta(hours=1)).astimezone(timezone.utc)
            add(f'scan_tokens/{historical_token}', ScanToken(
                event_id=event_id, created_by='synthetic-seed', created_at=token_created,
                expires_at=token_created + timedelta(hours=12), is_active=False,
            ), ['QR-09'])
        cursor = 0
        while cursor < len(people):
            group = people[cursor:cursor + rng.randint(1, 3)]
            cursor += len(group)
            manual = event.purchase_mode == EventPurchaseAccessType.ON_REQUEST or event.price == 0 or purchase_index % 7 == 0
            unit_cents = int(Decimal(str(event.price)) * 100)
            method = PaymentMethod.WEBSITE
            purchase_id = None
            if manual:
                method = (PaymentMethod.OMAGGIO, PaymentMethod.CASH, PaymentMethod.IBAN, PaymentMethod.PRIVATE_PAYPAL)[purchase_index % 4]
                if event.price == 0 or method == PaymentMethod.OMAGGIO:
                    unit_cents = 0
                    method = PaymentMethod.OMAGGIO
            else:
                purchase_id = f'syn-purchase-{purchase_index:06d}'
                order_id = f'SYNTHETIC-ORDER-{purchase_index:06d}'
                gross = len(group) * (unit_cents + int(Decimal(str(event.fee)) * 100))
                fee = min(150, gross)
                net = gross - fee
                payer = members[group[0][0]]
                purchase = EventPurchase(
                    payer_name=payer.name, payer_surname=payer.surname, payer_email=payer.email,
                    amount_total=money(gross), currency='EUR', paypal_fee=money(fee), net_amount=money(net),
                    transaction_id=f'SYNTHETIC-CAPTURE-{purchase_index:06d}', order_id=order_id,
                    status='COMPLETED', capture_status='COMPLETED', timestamp=creation.isoformat(),
                    ref_id=event_id, event_id=event_id, participants_count=len(group),
                    membership_ids=[mid for mid, _ in group], event_purchase_type=event.purchase_mode,
                    payment_method='paypal',
                )
                add(f'purchases/{purchase_id}', purchase, ['PAY-02', 'PAR-05', 'STA-04'])
                order_people = [{'name': members[mid].name, 'surname': members[mid].surname,
                                 'email': members[mid].email, 'phone': members[mid].phone,
                                 'birthdate': members[mid].birthdate} for mid, _ in group]
                add(f'orders/{order_id}', EventOrder(
                    order_id=order_id, order_status='COMPLETED', captured=True, purchase_id=purchase_id,
                    total=float(money(gross)), payment_method='paypal', event_id=event_id,
                    event_price=event.price, event_fee=event.fee, purchase_mode=event.purchase_mode,
                    participants=order_people, cart=[{'eventId': event_id, 'participants': order_people}],
                    created_at=creation,
                ), ['PAY-02', 'PAY-06'])
                for target in (ledger, expected):
                    target.update(purchases=1, paid_tickets=len(group), gross_cents=gross, net_cents=net, fee_cents=fee)
            for member_id, gender in group:
                member = members[member_id]
                participant_id = f'syn-participant-{member_id.removeprefix("syn-member-")}'
                entered = historical and rng.random() < 0.72
                manual_entry = entered and rng.random() < 0.2
                scanned_at = event_start + timedelta(minutes=rng.randrange(480)) if entered else None
                participant = EventParticipant(
                    event_id=event_id, name=member.name, surname=member.surname,
                    email=member.email, phone=member.phone, birthdate=member.birthdate,
                    membership_id=member_id, membership_included=True, purchase_id=purchase_id,
                    price=float(money(unit_cents)), payment_method=method, entered=entered,
                    entered_at=scanned_at, send_ticket_on_create=False,
                    gender=gender, gender_probability=1.0, newsletter_consent=member.newsletter_consent,
                    created_at=creation,
                )
                add(f'participants/{event_id}/participants_event/{participant_id}', participant,
                    ['PAR-14' if manual else 'PAR-05', 'QR-07' if manual_entry else 'QR-03'])
                member.attended_events.append(event_id)
                if purchase_id:
                    member.purchases.append(purchase_id)
                for target in (ledger, expected):
                    target.update(participants=1, entered=int(entered), manual_entries=int(manual_entry),
                                  omaggi=int(method == PaymentMethod.OMAGGIO))
                if entered:
                    add(f'entrance_scans/{event_id}/scans/{member_id}', EntranceScan(
                        scanned_at=scanned_at, scan_token=None if manual_entry else historical_token,
                        manual=bool(manual_entry), operator='synthetic-seed' if manual_entry else None,
                    ), ['QR-07' if manual_entry else 'QR-03', 'QR-15'])
            purchase_index += 1
        event.participants_count = len(people)
        event.max_participants = (None if index % 8 == 0 else
                                  len(people) if event.status == EventStatus.SOLD_OUT else len(people) + 50)
        add(f'events/{event_id}', event, ['EVT-01', 'EVT-05' if not people else 'EVT-04'])

    for member_id, member in members.items():
        member.purchases = sorted(set(member.purchases))
        member.attended_events = sorted(set(member.attended_events))
        add(f'memberships/{member_id}', member, ['MEM-01' if member.subscription_valid else 'MEM-02'])
    records.sort(key=lambda item: item['path'])
    isolated = []
    sample = next(item for item in records if item['path'].startswith('purchases/'))
    for field in ('status', 'capture_status'):
        for state in sorted(PurchaseStatus.invalid_statuses()):
            replacement = deepcopy(sample)
            replacement['data'][field] = state.value
            original = sample['data']
            isolated.append({
                'id': f'PAY-03-{field}-{state.value}', 'scenario_ids': ['PAY-03', 'STA-03', 'STA-05'],
                'field': field, 'state': state.value, 'execution': 'not_run', 'replace': [replacement],
                'instructions': 'Restore baseline before each case; retain linked participants and scans.',
                'expected_delta': {
                    'event_gross_cents': -int(Decimal(original['amount_total']) * 100),
                    'event_net_cents': -int(Decimal(original['net_amount']) * 100),
                    'event_paid_tickets': -original['participants_count'],
                    'participants': 0, 'entrances': 0,
                    'legacy_general_purchases': -1 if field == 'status' else 0,
                },
            })
    scenario_text = (ROOT / 'docs/superpowers/plans/2026-11-04-staging-synthetic-data.md').read_text()
    scenarios = re.findall(r'^\| ((?:MEM|EVT|PAR|PAY|DIS|QR|STA|OPS)-\d+) \|', scenario_text, re.M)
    represented = sorted({case for row in records for case in row['scenario_ids']})
    manifest = {
        'format_version': 1, 'seed': seed, 'as_of': as_of.isoformat(),
        'members': member_count, 'events': event_count, 'cohorts': dict(cohorts),
        'expected': {'global': dict(expected), 'events': {key: dict(value) for key, value in expected_events.items()},
                     'active_members': cohorts['active'], 'unique_members': member_count},
        'document_count': len(records), 'document_sha256': hashlib.sha256(encode(records).encode()).hexdigest(),
        'auth_accounts_created': 0, 'emails_sent': 0, 'provider_operations': 0,
        'historical_scanner_tokens_active': 0,
        'fixture_scenarios': represented,
        'api_cases': [{'id': scenario, 'status': 'not_run'} for scenario in scenarios],
        'limits': ['No cloud writer or Auth accounts; recipient allowlist is not expanded.',
                   'Fixtures do not prove API outcomes; Q contracts remain unresolved.',
                   'Historical entry times use the 22:00-06:00 Europe/Rome window.',
                   'Membership fees are manual history, not separate online purchases.'],
    }
    return {'records': records, 'manifest': manifest, 'isolated_cases': isolated}


def write_export(dataset, output):
    """Write private local artifacts only, with atomic replacement per file."""
    output = Path(output).resolve()
    private_root = (ROOT / '.local/staging').resolve()
    if output == private_root or not output.is_relative_to(private_root):
        raise ValueError('Output must be a subdirectory of .local/staging')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output, 0o700)
    artifacts = {
        'records.jsonl': ''.join(encode(row) + '\n' for row in dataset['records']),
        'isolated-cases.json': encode(dataset['isolated_cases']) + '\n',
        # Publish the checksum last: an interrupted mixed export fails validation.
        'manifest.json': encode(dataset['manifest']) + '\n',
    }
    for name, content in artifacts.items():
        destination = output / name
        if destination.is_symlink():
            raise ValueError('Refusing symlink output file')
        descriptor, temporary_name = tempfile.mkstemp(prefix=name + '.', suffix='.tmp', dir=output)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, 'w') as handle:
                handle.write(content)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    parser.add_argument('--recipients-config', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.local/staging/dataset')
    args = parser.parse_args()
    try:
        config = json.loads(args.recipients_config.read_text())
        # Use the explicitly approved base; do not print recipient values or add aliases to allowlist.
        base = config['allowed_recipients'][0]
        dataset = generate(seed=args.seed, as_of=args.as_of, email_base=base)
        write_export(dataset, args.output)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f'Generation failed ({type(error).__name__}); check local configuration.\n')
    print(json.dumps({'members': dataset['manifest']['members'], 'events': dataset['manifest']['events'],
                      'documents': dataset['manifest']['document_count'],
                      'expected': dataset['manifest']['expected']['global'],
                      'cloud_writes': 0, 'api_cases_executed': 0}))


if __name__ == '__main__':
    main()
