#!/usr/bin/env python3
"""Reconcile the mechanical findings of the 2026-11-28 production audit. Categories:

  events_status         events still `active` although they already ended        -> status `ended`
  memberships_validity  memberships `subscription_valid` for a past year          -> False (what the 1 January trigger
                        does; it had not invalidated them)
  participant_prices    participant `price` stored as text ("15")                 -> number
  purchase_memberships  purchase `membership_ids` pointing to deleted memberships -> those ids removed

Anything that needs a person's judgement (duplicate phones, missing emails, inconsistent discount-code counters) is only
LISTED under `review` in the plan, never changed.

Default is a DRY RUN: reads only, prints counts and writes a plan file (document paths and old/new values, no personal
data). `--apply --only CATEGORY[,CATEGORY]` writes nothing unless the plan file you pass is exactly what the live data
produces right now for those categories, and you confirm the project id. Every write changes ONE field, with a
precondition on the document's last update time, and a rollback file with the previous values is written first.

  python reconcile_stale_state.py --project mcp-website-2a1ad                  # dry run, writes the plan
  python reconcile_stale_state.py --project mcp-website-2a1ad --apply --only events_status,memberships_validity \\
      --plan-file PLAN.json --confirm-project mcp-website-2a1ad               # after reviewing the plan
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

sys.path.append(str(Path(__file__).resolve().parents[2]))
from domain.event_rules import EVENT_TIMEZONE, is_event_finished  # noqa: E402  (pure date logic, no Firebase import)

PROJECTS = {'mcp-website-2a1ad', 'mcp-website-dev-39539'}
CATEGORIES = ('events_status', 'memberships_validity', 'participant_prices', 'purchase_memberships')


def plan_events(documents, now):
    """documents: iterable of (id, data). Events still `active` whose end time has passed."""
    changes = []
    for doc_id, data in documents:
        if (data.get('status') or 'active') != 'active':
            continue
        event = SimpleNamespace(date=data.get('date'), start_time=data.get('startTime'), end_time=data.get('endTime'))
        if is_event_finished(event, now):
            changes.append(dict(category='events_status', path=f'events/{doc_id}', field='status', old='active', new='ended'))
    return changes


def plan_memberships(documents, year):
    """Returns (changes, manual_review). A membership is only touched when its year index is present and does not
    cover the current year; anything without that index is listed for a person to look at, never changed."""
    changes, manual = [], []
    for doc_id, data in documents:
        if data.get('subscription_valid') is not True:
            continue
        years = data.get('membership_years')
        usable = isinstance(years, list) and years and all(type(item) is int for item in years)
        if not usable:
            manual.append(doc_id)
        elif year not in years:
            changes.append(dict(category='memberships_validity', path=f'memberships/{doc_id}', field='subscription_valid',
                                old=True, new=False))
    return changes, manual


NUMBER = re.compile(r'\d+(?:\.\d+)?')


def plan_participant_prices(documents):
    """documents: (path, data). Text prices that are plain numbers become numbers; anything else is listed."""
    changes, manual = [], []
    for path, data in documents:
        price = data.get('price')
        if not isinstance(price, str):
            continue
        if NUMBER.fullmatch(price.strip()):
            changes.append(dict(category='participant_prices', path=path, field='price', old=price, new=float(price)))
        else:
            manual.append(path)
    return changes, manual


def plan_purchase_memberships(purchases, membership_ids):
    """purchases: (id, data). Drop only the ids of memberships that no longer exist."""
    changes = []
    for doc_id, data in purchases:
        ids = data.get('membership_ids')
        if isinstance(ids, list) and any(item not in membership_ids for item in ids):
            changes.append(dict(category='purchase_memberships', path=f'purchases/{doc_id}', field='membership_ids',
                                old=ids, new=[item for item in ids if item in membership_ids]))
    return changes


def review_items(memberships, participants, codes):
    """Ids only, for a person to decide; never changed by this script."""
    by_phone = {}
    for doc_id, data in memberships:
        phone = re.sub(r'\D', '', str(data.get('phone') or ''))
        if phone:
            by_phone.setdefault(phone, []).append(doc_id)
    used = {}
    for _, data in participants:
        if data.get('discountCodeId'):
            used[data['discountCodeId']] = used.get(data['discountCodeId'], 0) + 1
    return dict(
        memberships_without_email=sorted(doc_id for doc_id, data in memberships if not (data.get('email') or '').strip()),
        memberships_sharing_a_phone=sorted(sorted(ids) for ids in by_phone.values() if len(ids) > 1),
        discount_codes_with_inconsistent_counter=sorted(doc_id for doc_id, data in codes
                                                        if data.get('usedCount') != used.get(doc_id, 0)))


def build_plan(client, project, now):
    def read(source):
        return [(doc.id, doc.to_dict() or {}) for doc in source.stream()]
    events = read(client.collection('events'))
    members = read(client.collection('memberships'))
    purchases = read(client.collection('purchases'))
    codes = read(client.collection('discount_codes'))
    participants = [(doc.reference.path, doc.to_dict() or {}) for doc in client.collection_group('participants_event').stream()]
    member_changes, no_year_index = plan_memberships(members, now.year)
    price_changes, odd_prices = plan_participant_prices(participants)
    changes = (plan_events(events, now) + member_changes + price_changes
               + plan_purchase_memberships(purchases, {doc_id for doc_id, _ in members}))
    review = review_items(members, participants, codes)
    review.update(memberships_without_usable_year_index=sorted(no_year_index), participants_with_unparseable_price=sorted(odd_prices))
    return dict(project=project, year=now.year, changes=sorted(changes, key=lambda item: (item['category'], item['path'])),
                review=review)


def digest(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()


def selected(plan, only):
    return [change for change in plan['changes'] if change['category'] in only]


def apply_plan(client, plan, rollback_path):
    """One field per document, guarded by last_update_time; rollback file is on disk before the first write."""
    refs = []
    for change in plan['changes']:
        reference = client.document(change['path'])
        snapshot = reference.get()
        if not snapshot.exists or (snapshot.to_dict() or {}).get(change['field']) != change['old']:
            raise SystemExit(f"Stopped before any write: {change['path']} changed since the plan")
        refs.append((change, reference, snapshot.update_time))
    rollback_path.parent.mkdir(parents=True, exist_ok=True)
    rollback_path.write_text(json.dumps(plan['changes'], sort_keys=True, indent=1) + '\n')
    for change, reference, update_time in refs:
        reference.update({change['field']: change['new']}, option=client.write_option(last_update_time=update_time))
    return len(refs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project', required=True, choices=sorted(PROJECTS))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--only', help='comma separated categories to apply: ' + ', '.join(CATEGORIES))
    parser.add_argument('--plan-file', type=Path)
    parser.add_argument('--confirm-project')
    args = parser.parse_args()
    from google.cloud import firestore  # imported late so the pure planning functions stay testable offline
    client = firestore.Client(project=args.project)
    now = datetime.now(EVENT_TIMEZONE)
    plan = build_plan(client, args.project, now)
    for category in CATEGORIES:
        print(f"{category}: {len(selected(plan, {category}))} changes")
    for name, items in plan['review'].items():
        print(f"review/{name}: {len(items)} (listed in the plan, not changed)")
    if not args.apply:
        target = args.plan_file or Path('.local/reconcile') / f"plan-{args.project}-{now:%Y%m%d-%H%M}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(plan, sort_keys=True, indent=1) + '\n')
        print(f"Dry run: nothing written to the database. Plan saved to {target} (digest {digest(plan)[:12]}).")
        return 0
    if args.confirm_project != args.project or not args.plan_file:
        raise SystemExit('--apply needs --plan-file from a reviewed dry run and --confirm-project equal to --project')
    only = set((args.only or '').split(',')) - {''}
    if not only or not only <= set(CATEGORIES):
        raise SystemExit('--apply needs --only with one or more of: ' + ', '.join(CATEGORIES))
    reviewed = json.loads(args.plan_file.read_text())
    if digest(selected(reviewed, only)) != digest(selected(plan, only)):
        raise SystemExit('The live data no longer matches the reviewed plan: run the dry run again and review it.')
    rollback = Path('.local/reconcile') / f"rollback-{args.project}-{now:%Y%m%d-%H%M%S}.json"
    print(f"Applied {apply_plan(client, dict(plan, changes=selected(plan, only)), rollback)} single-field updates. "
          f"Rollback values: {rollback}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
