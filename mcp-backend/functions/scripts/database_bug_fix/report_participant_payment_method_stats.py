import argparse
import os
import sys
from collections import Counter
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
        description="Report participants counts and why payment_method is/ is not updated."
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit participants scanned.")
    args = parser.parse_args()

    counts = {
        "total": 0,
        "would_update_missing_payment_method": 0,
        "skipped_has_payment_method": 0,
        "missing_with_purchase_id": 0,
        "missing_without_purchase_id": 0,
    }
    method_counts = Counter()
    missing_assignments = Counter()

    stream = db.collection_group("participants_event").stream()

    for snap in _iter_limited(stream, args.limit):
        data = snap.to_dict() or {}
        counts["total"] += 1

        payment_method = (data.get("payment_method") or data.get("paymentMethod") or "").strip().lower()
        purchase_id = data.get("purchase_id") or data.get("purchaseId")
        price_value = _parse_price(data.get("price"))

        if payment_method:
            counts["skipped_has_payment_method"] += 1
            method_counts[payment_method] += 1
            continue

        counts["would_update_missing_payment_method"] += 1
        if purchase_id:
            counts["missing_with_purchase_id"] += 1
            missing_assignments["website"] += 1
        elif price_value == 0:
            counts["missing_without_purchase_id"] += 1
            missing_assignments["omaggio"] += 1
        else:
            counts["missing_without_purchase_id"] += 1
            missing_assignments["iban"] += 1

    print(f"[participants_total] {counts['total']}")
    print(f"[would_update_missing_payment_method] {counts['would_update_missing_payment_method']}")
    print(f"[skipped_has_payment_method] {counts['skipped_has_payment_method']}")
    print(f"[missing_with_purchase_id] {counts['missing_with_purchase_id']}")
    print(f"[missing_without_purchase_id] {counts['missing_without_purchase_id']}")

    print("\n[payment_method_breakdown]")
    for method, count in method_counts.most_common():
        print(f"  {method}: {count}")

    print("\n[missing_payment_method_assigned_as]")
    for method, count in missing_assignments.most_common():
        print(f"  {method}: {count}")


if __name__ == "__main__":
    main()
