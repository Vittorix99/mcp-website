import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from itertools import islice

from google.cloud import firestore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db
from utils.events_utils import normalize_email, normalize_phone


def _iter_limited(stream, limit):
    if limit is None:
        yield from stream
        return
    yield from islice(stream, limit)


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        pass
    try:
        return datetime.strptime(str(value), "%d-%m-%Y")
    except Exception:
        return None


def _choose_canonical(docs):
    def sort_key(item):
        doc = item[1]
        data = doc.to_dict() or {}
        valid = bool(data.get("subscription_valid"))
        end_dt = _parse_date(data.get("end_date"))
        start_dt = _parse_date(data.get("start_date"))
        return (valid, end_dt or datetime.min, start_dt or datetime.min)

    return max(docs, key=sort_key)


def rebuild_attended_events(dry_run=False):
    mapping = defaultdict(set)
    phone_events = defaultdict(set)
    stream = db.collection_group("participants_event").stream()
    for snap in stream:
        data = snap.to_dict() or {}
        membership_id = data.get("membershipId") or data.get("membership_id")
        if not membership_id:
            continue
        event_id = data.get("event_id")
        if not event_id:
            # path: participants/{eventId}/participants_event/{id}
            parts = snap.reference.path.split("/")
            if len(parts) >= 2:
                event_id = parts[1]
        if event_id:
            mapping[membership_id].add(event_id)
            phone = normalize_phone(data.get("phone"))
            if phone:
                phone_events[phone].add(event_id)

    batch = db.batch()
    writes = 0
    for membership_id, events in mapping.items():
        if dry_run:
            print(f"[attended_events] {membership_id} -> {sorted(events)}")
            continue
        ref = db.collection("memberships").document(membership_id)
        batch.update(ref, {"attended_events": sorted(events)})
        writes += 1
        if writes % 450 == 0:
            batch.commit()
            batch = db.batch()
    if not dry_run and writes % 450:
        batch.commit()
    return mapping, phone_events


def cleanup_memberships(dry_run=False, limit=None):
    attended_by_membership, phone_events = rebuild_attended_events(dry_run=dry_run)

    docs = list(_iter_limited(db.collection("memberships").stream(), limit))
    by_email = defaultdict(list)
    for doc in docs:
        data = doc.to_dict() or {}
        email = normalize_email(data.get("email"))
        if email:
            by_email[email].append(doc)

    for email, entries in by_email.items():
        if len(entries) < 2:
            continue
        for doc in entries:
            data = doc.to_dict() or {}
            attended = attended_by_membership.get(doc.id)
            if attended is None:
                attended = set(data.get("attended_events") or [])
            if len(attended) > 0:
                continue
            name = (data.get("name") or "").strip()
            surname = (data.get("surname") or "").strip()
            if dry_run:
                print(f"[clear_email] {doc.id} ({name} {surname} <{email}>)")
            else:
                doc.reference.update({"email": None})

    repaired = []
    for doc in docs:
        data = doc.to_dict() or {}
        attended = attended_by_membership.get(doc.id)
        if attended is None:
            attended = set(data.get("attended_events") or [])
        if len(attended) > 0:
            continue
        phone = normalize_phone(data.get("phone"))
        if not phone:
            continue
        events = phone_events.get(phone)
        if not events:
            continue
        name = (data.get("name") or "").strip()
        surname = (data.get("surname") or "").strip()
        if dry_run:
            print(
                f"[repair_attended] {doc.id} "
                f"({name} {surname} phone={phone}) -> {sorted(events)}"
            )
        else:
            doc.reference.update({"attended_events": sorted(events)})
        attended_by_membership[doc.id] = set(events)
        repaired.append(doc.id)

    zero_attended = []
    for doc in docs:
        data = doc.to_dict() or {}
        attended = attended_by_membership.get(doc.id)
        if attended is None:
            attended = set(data.get("attended_events") or [])
        if len(attended) == 0:
            name = (data.get("name") or "").strip()
            surname = (data.get("surname") or "").strip()
            email = normalize_email(data.get("email"))
            phone = (data.get("phone") or "").strip()
            zero_attended.append((doc.id, name, surname, email, phone))

    print(f"[zero_attended] count={len(zero_attended)}")
    for member_id, name, surname, email, phone in zero_attended:
        print(
            f"[zero_attended] {member_id} "
            f"({name} {surname} <{email}> phone={phone})"
        )


def main():
    parser = argparse.ArgumentParser(description="Rebuild attended_events and clear duplicate emails.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing.")
    parser.add_argument("--limit", type=int, default=None, help="Limit memberships scanned.")
    args = parser.parse_args()

    cleanup_memberships(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
