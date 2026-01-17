import argparse
import os
import sys
from itertools import islice

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.firebase_config import db


def _iter_limited(stream, limit):
    if limit is None:
        yield from stream
        return
    yield from islice(stream, limit)


def _parse_price(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Set payment_method=omaggio for participants with price 0."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing.")
    parser.add_argument("--limit", type=int, default=None, help="Limit participants scanned.")
    args = parser.parse_args()

    participants = db.collection_group("participants_event").stream()
    updates = []
    matched = 0

    for snap in _iter_limited(participants, args.limit):
        data = snap.to_dict() or {}
        price_value = _parse_price(data.get("price"))
        if price_value != 0:
            continue

        purchase_id = data.get("purchase_id") or data.get("purchaseId")
        if purchase_id:
            continue

        payment_method = (data.get("payment_method") or data.get("paymentMethod") or "").strip().lower()
        if payment_method == "omaggio":
            continue

        name = (data.get("name") or "").strip()
        surname = (data.get("surname") or "").strip()
        contact = data.get("email") or data.get("phone") or "-"

        matched += 1
        if args.dry_run:
            print(
                f"[omaggio] {snap.reference.path} "
                f"{name} {surname} <{contact}> payment_method={payment_method or '-'}"
            )
        else:
            updates.append(snap.reference)

    if args.dry_run:
        print(f"[summary] updates={matched}")
        return

    if not updates:
        print("[summary] updates=0")
        return

    batch = db.batch()
    count = 0
    for ref in updates:
        batch.update(ref, {"payment_method": "omaggio"})
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()

    if count % 400 != 0:
        batch.commit()

    print(f"[summary] updates={count}")


if __name__ == "__main__":
    main()
