import argparse
import os
import sys
from datetime import datetime, timezone
from itertools import islice

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db
from models.enums import PurchaseTypes
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
        return value
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


def _parse_purchase_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "")).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _find_existing_membership(email, phone):
    candidates = []
    if email:
        candidates = db.collection("memberships").where(filter=FieldFilter("email", "==", email)).limit(2).get()
    if phone and not candidates:
        candidates = db.collection("memberships").where(filter=FieldFilter("phone", "==", phone)).limit(2).get()
    if not candidates:
        return None, None
    if len(candidates) > 1:
        return None, "ambiguous"
    return candidates[0], None


def main():
    parser = argparse.ArgumentParser(
        description="Fix participants missing membershipId despite having purchase_id."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing.")
    parser.add_argument("--limit", type=int, default=None, help="Limit participants scanned.")
    args = parser.parse_args()

    events_cache = {}
    purchases_cache = {}
    participants = db.collection_group("participants_event").stream()

    missing = []
    for snap in _iter_limited(participants, args.limit):
        data = snap.to_dict() or {}
        purchase_id = data.get("purchase_id") or data.get("purchaseId")
        membership_id = data.get("membershipId") or data.get("membership_id")
        if purchase_id and not membership_id:
            missing.append((snap, data, purchase_id))

    print(f"[missing_membership] count={len(missing)}")

    for snap, data, purchase_id in missing:
        name = (data.get("name") or "").strip()
        surname = (data.get("surname") or "").strip()
        email = normalize_email(data.get("email"))
        phone = normalize_phone(data.get("phone"))
        birthdate = data.get("birthdate")
        event_id = _get_event_id(data, snap.reference.path)

        event_date = None
        if event_id:
            if event_id not in events_cache:
                ev_doc = db.collection("events").document(event_id).get()
                events_cache[event_id] = ev_doc.to_dict() if ev_doc.exists else {}
            event_date = _parse_event_date(events_cache[event_id].get("date"))

        purchase_date = None
        if purchase_id:
            if purchase_id not in purchases_cache:
                p_doc = db.collection("purchases").document(purchase_id).get()
                purchases_cache[purchase_id] = p_doc.to_dict() if p_doc.exists else {}
            p_data = purchases_cache[purchase_id]
            purchase_date = _parse_purchase_date(
                p_data.get("timestamp") or p_data.get("createdAt") or p_data.get("created_at")
            )

        existing, issue = _find_existing_membership(email, phone)
        if issue == "ambiguous":
            print(
                f"[skip_ambiguous] {snap.reference.path} "
                f"{name} {surname} <{email or phone}>"
            )
            continue

        if existing:
            if args.dry_run:
                print(
                    f"[link_existing] {snap.reference.path} "
                    f"{name} {surname} <{email or phone}> -> {existing.id}"
                )
                continue

            update_payload = {
                "membershipId": existing.id,
                "membership_id": existing.id,
                "membership_included": True,
            }
            snap.reference.update(update_payload)
            db.collection("memberships").document(existing.id).update(
                {
                    "attended_events": firestore.ArrayUnion([event_id]) if event_id else firestore.ArrayUnion([]),
                    "purchases": firestore.ArrayUnion([purchase_id]),
                }
            )
            continue

        start_dt = purchase_date or event_date or datetime.now(timezone.utc)
        start_date = start_dt.isoformat()
        end_date = calculate_end_of_year_membership(start_dt)

        payload = {
            "name": name,
            "surname": surname,
            "email": email or None,
            "phone": phone or None,
            "birthdate": birthdate,
            "start_date": start_date,
            "end_date": end_date,
            "subscription_valid": True,
            "membership_sent": False,
            "membership_type": PurchaseTypes.EVENT.value,
            "purchase_id": purchase_id,
            "purchases": [purchase_id],
            "attended_events": [event_id] if event_id else [],
            "send_card_on_create": False,
        }

        if args.dry_run:
            print(
                f"[create_membership] {snap.reference.path} "
                f"{name} {surname} <{email or phone}> "
                f"purchase_id={purchase_id} event_id={event_id}"
            )
            continue

        ref = db.collection("memberships").add(payload)[1]
        snap.reference.update(
            {
                "membershipId": ref.id,
                "membership_id": ref.id,
                "membership_included": True,
            }
        )
        print(
            f"[created] {ref.id} for {snap.reference.path} "
            f"{name} {surname} <{email or phone}>"
        )


if __name__ == "__main__":
    main()
