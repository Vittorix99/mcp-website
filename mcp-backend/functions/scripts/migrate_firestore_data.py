import argparse
import os
import sys
from itertools import islice

from google.cloud.firestore_v1 import DELETE_FIELD

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.firebase_config import db


def _iter_limited(stream, limit):
    if limit is None:
        yield from stream
        return
    yield from islice(stream, limit)


def _commit_batch(batch, writes, dry_run):
    if dry_run or writes == 0:
        return
    batch.commit()


def migrate_participants(dry_run=False, limit=None):
    updates = 0
    batch = db.batch()
    writes = 0
    stream = db.collection_group("participants_event").stream()

    for snap in _iter_limited(stream, limit):
        data = snap.to_dict() or {}
        current_method = data.get("payment_method")
        if current_method:
            continue
        purchase_id = data.get("purchase_id")
        payment_method = "website" if purchase_id else "iban"
        if dry_run:
            print(f"[participants] {snap.reference.path} -> payment_method={payment_method}")
        else:
            batch.update(snap.reference, {"payment_method": payment_method})
            writes += 1
            if writes % 450 == 0:
                batch.commit()
                batch = db.batch()
        updates += 1

    _commit_batch(batch, writes % 450, dry_run)
    return updates


def _collect_purchase_stats(limit=None):
    stats = {}
    stream = db.collection_group("participants_event").stream()
    for snap in _iter_limited(stream, limit):
        data = snap.to_dict() or {}
        purchase_id = data.get("purchase_id")
        if not purchase_id:
            continue
        entry = stats.setdefault(purchase_id, {"count": 0, "membership_ids": set()})
        entry["count"] += 1
        membership_id = data.get("membershipId") or data.get("membership_id")
        if membership_id:
            entry["membership_ids"].add(membership_id)
    return stats


def migrate_purchases(dry_run=False, limit=None, force=False):
    stats = _collect_purchase_stats()
    updates = 0
    batch = db.batch()
    writes = 0
    stream = db.collection("purchases").stream()

    for snap in _iter_limited(stream, limit):
        data = snap.to_dict() or {}
        purchase_id = snap.id
        if purchase_id not in stats and not force:
            continue
        entry = stats.get(purchase_id, {"count": 0, "membership_ids": set()})
        desired_count = entry["count"]
        desired_membership_ids = sorted(entry["membership_ids"])

        update_payload = {}
        current_count = data.get("participants_count")
        if force or current_count is None or current_count != desired_count:
            update_payload["participants_count"] = desired_count

        current_membership_ids = data.get("membership_ids") or []
        if force or sorted(current_membership_ids) != desired_membership_ids:
            update_payload["membership_ids"] = desired_membership_ids

        if not update_payload:
            continue

        if dry_run:
            print(f"[purchases] {snap.reference.path} -> {update_payload}")
        else:
            batch.update(snap.reference, update_payload)
            writes += 1
            if writes % 450 == 0:
                batch.commit()
                batch = db.batch()
        updates += 1

    _commit_batch(batch, writes % 450, dry_run)
    return updates


def migrate_events(dry_run=False, limit=None):
    updates = 0
    batch = db.batch()
    writes = 0
    stream = db.collection("events").stream()
    legacy_fields = ["active", "membershipFee", "membership_fee", "description"]

    for snap in _iter_limited(stream, limit):
        data = snap.to_dict() or {}
        update_payload = {}

        status = data.get("status")
        if not status:
            if "active" in data:
                update_payload["status"] = "active" if data.get("active") else "ended"
            else:
                update_payload["status"] = "active"

        for field in legacy_fields:
            if field in data:
                update_payload[field] = DELETE_FIELD

        if not update_payload:
            continue

        if dry_run:
            print(f"[events] {snap.reference.path} -> {update_payload}")
        else:
            batch.update(snap.reference, update_payload)
            writes += 1
            if writes % 450 == 0:
                batch.commit()
                batch = db.batch()
        updates += 1

    _commit_batch(batch, writes % 450, dry_run)
    return updates


def main():
    parser = argparse.ArgumentParser(description="Backfill Firestore data for new schemas.")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing derived fields.")
    parser.add_argument("--limit", type=int, default=None, help="Limit documents per collection.")
    parser.add_argument("--participants", action="store_true", help="Update participants payment_method.")
    parser.add_argument("--purchases", action="store_true", help="Update purchases participants_count/membership_ids.")
    parser.add_argument("--events", action="store_true", help="Update events status/remove legacy fields.")

    args = parser.parse_args()
    run_all = not (args.participants or args.purchases or args.events)

    if run_all or args.participants:
        count = migrate_participants(dry_run=args.dry_run, limit=args.limit)
        print(f"Participants updated: {count}")

    if run_all or args.purchases:
        count = migrate_purchases(dry_run=args.dry_run, limit=args.limit, force=args.force)
        print(f"Purchases updated: {count}")

    if run_all or args.events:
        count = migrate_events(dry_run=args.dry_run, limit=args.limit)
        print(f"Events updated: {count}")


if __name__ == "__main__":
    main()
