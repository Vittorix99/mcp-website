import argparse
import os
import sys
from collections import defaultdict
from itertools import islice

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db
from utils.events_utils import normalize_email, normalize_phone


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


def main():
    parser = argparse.ArgumentParser(
        description="Report discrepancies between membership docs and participants_event."
    )
    parser.add_argument("--limit-participants", type=int, default=None)
    parser.add_argument("--limit-memberships", type=int, default=None)
    args = parser.parse_args()

    participants = db.collection_group("participants_event").stream()

    events_by_membership = defaultdict(set)
    purchases_by_membership = defaultdict(set)
    missing_membership_id = []

    for snap in _iter_limited(participants, args.limit_participants):
        data = snap.to_dict() or {}
        purchase_id = data.get("purchase_id") or data.get("purchaseId")
        membership_id = data.get("membershipId") or data.get("membership_id")
        event_id = _get_event_id(data, snap.reference.path)

        if purchase_id and not membership_id:
            missing_membership_id.append({
                "path": snap.reference.path,
                "purchase_id": purchase_id,
                "name": (data.get("name") or "").strip(),
                "surname": (data.get("surname") or "").strip(),
                "email": normalize_email(data.get("email")),
                "phone": normalize_phone(data.get("phone")),
            })
            continue

        if membership_id:
            if event_id:
                events_by_membership[membership_id].add(event_id)
            if purchase_id:
                purchases_by_membership[membership_id].add(purchase_id)

    memberships = db.collection("memberships").stream()
    discrepancies = []

    for snap in _iter_limited(memberships, args.limit_memberships):
        data = snap.to_dict() or {}
        membership_id = snap.id
        stored_events = set(data.get("attended_events") or [])
        stored_purchases = set(data.get("purchases") or [])

        derived_events = events_by_membership.get(membership_id, set())
        derived_purchases = purchases_by_membership.get(membership_id, set())

        missing_events = sorted(derived_events - stored_events)
        missing_purchases = sorted(derived_purchases - stored_purchases)
        extra_events = sorted(stored_events - derived_events)
        extra_purchases = sorted(stored_purchases - derived_purchases)

        if missing_events or missing_purchases or extra_events or extra_purchases:
            discrepancies.append({
                "id": membership_id,
                "name": (data.get("name") or "").strip(),
                "surname": (data.get("surname") or "").strip(),
                "email": normalize_email(data.get("email")),
                "phone": normalize_phone(data.get("phone")),
                "stored_events": sorted(stored_events),
                "derived_events": sorted(derived_events),
                "stored_purchases": sorted(stored_purchases),
                "derived_purchases": sorted(derived_purchases),
                "missing_events": missing_events,
                "missing_purchases": missing_purchases,
                "extra_events": extra_events,
                "extra_purchases": extra_purchases,
            })

    print(f"[missing_membership_id] count={len(missing_membership_id)}")
    for item in missing_membership_id:
        print(
            f"[missing_membership_id] {item['path']} "
            f"purchase_id={item['purchase_id']} "
            f"{item['name']} {item['surname']} <{item['email'] or item['phone']}>"
        )

    print(f"[membership_discrepancies] count={len(discrepancies)}")
    for item in discrepancies:
        label = f"{item['name']} {item['surname']} <{item['email'] or item['phone']}>"
        print(f"[membership_discrepancies] {item['id']} {label}")
        print(f"  stored_events={item['stored_events']}")
        print(f"  derived_events={item['derived_events']}")
        print(f"  stored_purchases={item['stored_purchases']}")
        print(f"  derived_purchases={item['derived_purchases']}")
        if item["missing_events"]:
            print(f"  missing_events={item['missing_events']}")
        if item["missing_purchases"]:
            print(f"  missing_purchases={item['missing_purchases']}")
        if item["extra_events"]:
            print(f"  extra_events={item['extra_events']}")
        if item["extra_purchases"]:
            print(f"  extra_purchases={item['extra_purchases']}")


if __name__ == "__main__":
    main()
