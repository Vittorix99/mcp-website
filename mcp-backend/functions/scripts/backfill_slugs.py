import argparse
import os
import sys

# Allow running from repo root by adding functions/ to sys.path
FUNCTIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if FUNCTIONS_DIR not in sys.path:
    sys.path.insert(0, FUNCTIONS_DIR)

from config.firebase_config import db
from utils.slug_utils import build_slug


def backfill_collection(name, make_slug, dry_run=False, limit=None):
    collection = db.collection(name)
    stream = collection.stream()
    updated = 0
    scanned = 0

    for doc in stream:
        scanned += 1
        data = doc.to_dict() or {}
        if data.get("slug"):
            continue
        slug = make_slug(doc.id, data)
        if not slug:
            continue
        if dry_run:
            print(f"[DRY-RUN] {name}/{doc.id} -> {slug}")
        else:
            collection.document(doc.id).update({"slug": slug})
            print(f"[UPDATED] {name}/{doc.id} -> {slug}")
        updated += 1
        if limit and updated >= limit:
            break

    print(f"[DONE] {name}: scanned={scanned} updated={updated}")


def event_slug(doc_id, data):
    title = data.get("title", "")
    date = data.get("date", "")
    seed = f"{title} {date}".strip()
    return build_slug(seed, suffix=doc_id[-6:])


def membership_slug(doc_id, data):
    name = data.get("name", "")
    surname = data.get("surname", "")
    return build_slug(name, surname, suffix=doc_id[-6:])


def purchase_slug(doc_id, data):
    payer_name = data.get("payer_name", "")
    payer_surname = data.get("payer_surname", "")
    return build_slug(payer_name, payer_surname, suffix=doc_id[-6:])


def main():
    parser = argparse.ArgumentParser(description="Backfill slug fields in Firestore.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--limit", type=int, default=None, help="Max updates per collection.")
    parser.add_argument("--events", action="store_true", help="Backfill events.")
    parser.add_argument("--memberships", action="store_true", help="Backfill memberships.")
    parser.add_argument("--purchases", action="store_true", help="Backfill purchases.")
    args = parser.parse_args()

    if not (args.events or args.memberships or args.purchases):
        args.events = args.memberships = args.purchases = True

    if args.events:
        backfill_collection("events", event_slug, dry_run=args.dry_run, limit=args.limit)
    if args.memberships:
        backfill_collection("memberships", membership_slug, dry_run=args.dry_run, limit=args.limit)
    if args.purchases:
        backfill_collection("purchases", purchase_slug, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
