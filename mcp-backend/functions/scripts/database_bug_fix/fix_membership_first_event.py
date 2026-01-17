import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import islice

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db
from utils.events_utils import calculate_end_of_year_membership, normalize_email, normalize_phone


def _iter_limited(stream, limit):
    if limit is None:
        yield from stream
        return
    yield from islice(stream, limit)


def _get_event_id(data, ref_path):
    if data.get("event_id"):
        return data.get("event_id")
    parts = ref_path.split("/")
    if len(parts) >= 2 and parts[0] == "participants":
        return parts[1]
    return None


def _parse_event_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc)
    s = str(value).strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "")).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Fix membership purchase_id/start_date based on earliest attended event."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing.")
    parser.add_argument("--limit-participants", type=int, default=None)
    parser.add_argument("--limit-memberships", type=int, default=None)
    args = parser.parse_args()

    participants = db.collection_group("participants_event").stream()
    by_membership = defaultdict(list)
    for snap in _iter_limited(participants, args.limit_participants):
        data = snap.to_dict() or {}
        membership_id = data.get("membershipId") or data.get("membership_id")
        if not membership_id:
            continue
        event_id = _get_event_id(data, snap.reference.path)
        if not event_id:
            continue
        by_membership[membership_id].append(
            {
                "event_id": event_id,
                "purchase_id": data.get("purchase_id") or data.get("purchaseId"),
                "created_at": data.get("createdAt"),
            }
        )

    events_cache = {}
    purchases_cache = {}

    def get_event_date(event_id):
        if event_id not in events_cache:
            snap = db.collection("events").document(event_id).get()
            events_cache[event_id] = snap.to_dict() if snap.exists else {}
        return _parse_event_date(events_cache[event_id].get("date"))

    def get_purchase_event_id(purchase_id):
        if purchase_id not in purchases_cache:
            snap = db.collection("purchases").document(purchase_id).get()
            purchases_cache[purchase_id] = snap.to_dict() if snap.exists else {}
        return purchases_cache[purchase_id].get("ref_id")

    memberships = db.collection("memberships").stream()
    updates = 0

    for snap in _iter_limited(memberships, args.limit_memberships):
        data = snap.to_dict() or {}
        membership_id = snap.id
        participants_info = by_membership.get(membership_id) or []
        if not participants_info:
            continue

        earliest = None
        for info in participants_info:
            event_date = get_event_date(info["event_id"])
            if not event_date:
                continue
            if earliest is None or event_date < earliest["event_date"]:
                earliest = {
                    "event_id": info["event_id"],
                    "event_date": event_date,
                    "purchase_id": info.get("purchase_id"),
                }

        if not earliest or not earliest.get("purchase_id"):
            continue

        current_purchase_id = data.get("purchase_id")
        if not current_purchase_id:
            continue

        current_event_id = get_purchase_event_id(current_purchase_id)
        current_event_date = get_event_date(current_event_id) if current_event_id else None
        if not current_event_date:
            continue

        if earliest["event_date"] >= current_event_date:
            continue

        name = (data.get("name") or "").strip()
        surname = (data.get("surname") or "").strip()
        contact = normalize_email(data.get("email")) or normalize_phone(data.get("phone"))

        new_start = earliest["event_date"].isoformat()
        new_end = calculate_end_of_year_membership(earliest["event_date"])

        if args.dry_run:
            print(
                f"[fix] {membership_id} {name} {surname} <{contact}> "
                f"purchase_id {current_purchase_id} ({current_event_id}) -> "
                f"{earliest['purchase_id']} ({earliest['event_id']}) "
                f"start_date {data.get('start_date')} -> {new_start}"
            )
        else:
            snap.reference.update(
                {
                    "purchase_id": earliest["purchase_id"],
                    "start_date": new_start,
                    "end_date": new_end,
                }
            )
        updates += 1

    print(f"[fixed] count={updates}")


if __name__ == "__main__":
    main()
