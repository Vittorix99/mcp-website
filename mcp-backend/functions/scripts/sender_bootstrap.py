"""
Bootstrap Sender from Firestore data.

Groups created / populated:
  - Memberships          → all docs in `memberships`
  - Newsletter           → docs in `newsletter_consents` (active=True)
  - Participant-{title}  → same newsletter consents, one group per event title

Usage:
  python sender_bootstrap.py [--dry-run] [--limit N] [--skip-memberships] [--skip-participants]

Requirements:
  - SENDER_API_KEY in mcp-backend/functions/.env (or already exported)
  - Firebase credentials configured (GOOGLE_APPLICATION_CREDENTIALS or ADC)
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from itertools import cycle
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env before importing anything that reads env vars
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path, override=False)

from config.firebase_config import db  # noqa: E402
from services.sender.sender_service import SenderService  # noqa: E402
from utils.events_utils import normalize_email  # noqa: E402


# ------------------------------------------------------------------ #
# Progress helper
# ------------------------------------------------------------------ #

class Progress:
    def __init__(self, label: str, total: Optional[int] = None):
        self.label = label
        self.total = total
        self.count = 0
        self._spinner = cycle("|/-\\")

    def update(self, step: int = 1):
        self.count += step
        if self.total:
            pct = min(self.count / self.total, 1.0)
            width = 30
            filled = int(pct * width)
            bar = "#" * filled + "-" * (width - filled)
            line = f"{self.label}: [{bar}] {self.count}/{self.total} ({pct*100:5.1f}%)"
        else:
            spin = next(self._spinner)
            line = f"{self.label}: {spin} {self.count}"
        sys.stdout.write("\r" + line)
        sys.stdout.flush()

    def done(self):
        if self.total:
            pct = min(self.count / self.total, 1.0)
            width = 30
            filled = int(pct * width)
            bar = "#" * filled + "-" * (width - filled)
            line = f"{self.label}: [{bar}] {self.count}/{self.total} ({pct*100:5.1f}%)"
        else:
            line = f"{self.label}: done ({self.count})"
        sys.stdout.write("\r" + line + "\n")
        sys.stdout.flush()


# ------------------------------------------------------------------ #
# Firestore pagination
# ------------------------------------------------------------------ #

def _paged_stream(
    collection,
    limit: Optional[int] = None,
    batch_size: int = 200,
    offset: int = 0,
    single_shot: bool = False,
):
    if single_shot:
        fetched = 0
        skipped = 0
        try:
            docs = collection.order_by("__name__").stream()
        except Exception as e:
            print(f"[firestore] single-shot stream failed: {e}")
            return
        for doc in docs:
            if offset and skipped < offset:
                skipped += 1
                continue
            yield doc
            fetched += 1
            if limit is not None and fetched >= limit:
                return
        return

    fetched = 0
    skipped = 0
    last_doc = None
    while True:
        query = collection.order_by("__name__").limit(batch_size)
        if last_doc is not None:
            query = query.start_after(last_doc)
        try:
            docs = list(query.stream())
        except Exception as e:
            print(f"[firestore] stream batch failed: {e}")
            return
        if not docs:
            return
        for doc in docs:
            last_doc = doc
            if offset and skipped < offset:
                skipped += 1
                continue
            yield doc
            fetched += 1
            if limit is not None and fetched >= limit:
                return


# ------------------------------------------------------------------ #
# Group find-or-create (mirrors sender_sync._find_or_create_group)
# ------------------------------------------------------------------ #

def _find_or_create_group(svc: SenderService, title: str, group_cache: Dict[str, str], dry_run: bool) -> Optional[str]:
    """Return group ID for title, using cache. Creates if missing."""
    key = title.strip().lower()
    if key in group_cache:
        return group_cache[key]

    payload = svc.list_groups()
    groups = payload.get("data", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
    for g in groups:
        if str(g.get("title", "")).strip().lower() == key:
            gid = str(g["id"])
            group_cache[key] = gid
            return gid

    if dry_run:
        print(f"\n[groups] would create '{title}' (dry-run)")
        group_cache[key] = f"dry-run-{key}"
        return group_cache[key]

    new_payload = svc.create_group(title)
    if new_payload:
        gid = (new_payload.get("data") or {}).get("id") or new_payload.get("id")
        if gid:
            gid = str(gid)
            group_cache[key] = gid
            print(f"\n[groups] created '{title}' -> {gid}")
            return gid

    print(f"\n[groups] ERROR: could not create group '{title}'")
    return None


# ------------------------------------------------------------------ #
# Upsert + group assignment
# ------------------------------------------------------------------ #

def _upsert(
    svc: SenderService,
    email: str,
    firstname: Optional[str],
    lastname: Optional[str],
    phone: Optional[str],
    group_ids: List[str],
    dry_run: bool,
    email_cache: Dict[str, bool],
    no_phone: bool = False,
):
    def _sanitize_phone(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        # keep digits and leading +
        cleaned = re.sub(r"[^\d+]", "", raw)
        if cleaned.startswith("00"):
            cleaned = "+" + cleaned[2:]
        if not cleaned.startswith("+"):
            return None
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 8:
            return None
        return cleaned

    if not email:
        return
    if dry_run:
        print(f"\n[sender] would upsert {email} -> groups={group_ids}")
        return
    if email_cache.get(email):
        # Already upserted this session — just assign extra groups
        for gid in group_ids:
            if gid and not gid.startswith("dry-run"):
                svc.add_to_group(email, gid)
        return
    try:
        valid_groups = [g for g in group_ids if g and not g.startswith("dry-run")]
        phone_to_send = None if no_phone else _sanitize_phone(phone)
        result = svc.upsert_subscriber(
            email=email,
            firstname=firstname or None,
            lastname=lastname or None,
            phone=phone_to_send,
            groups=valid_groups if valid_groups else None,
        )
        if result is None and phone_to_send:
            # Common Sender validation failure: invalid phone format.
            print(f"\n[sender] retry without phone for {email}")
            result = svc.upsert_subscriber(
                email=email,
                firstname=firstname or None,
                lastname=lastname or None,
                phone=None,
                groups=valid_groups if valid_groups else None,
            )
        if result is None:
            print(f"\n[sender] upsert failed for {email}")
            return
        email_cache[email] = True
    except Exception as exc:
        print(f"\n[sender] upsert failed for {email}: {exc}")


# ------------------------------------------------------------------ #
# Event title cache
# ------------------------------------------------------------------ #

def _get_event_title(event_id: str, event_cache: Dict[str, str]) -> str:
    if event_id in event_cache:
        return event_cache[event_id]
    try:
        doc = db.collection("events").document(event_id).get()
        title = (doc.to_dict() or {}).get("title", "") if doc.exists else ""
    except Exception as e:
        print(f"\n[events] fetch failed for {event_id}: {e}")
        title = ""
    event_cache[event_id] = title
    return title


# ------------------------------------------------------------------ #
# Firestore iterators
# ------------------------------------------------------------------ #

def iter_memberships(
    limit: Optional[int] = None,
    offset: int = 0,
    batch_size: int = 200,
    single_shot: bool = False,
):
    stream = _paged_stream(
        db.collection("memberships"),
        limit=limit,
        batch_size=batch_size,
        offset=offset,
        single_shot=single_shot,
    )
    for snap in stream:
        data = snap.to_dict() or {}
        email = normalize_email(data.get("email"))
        if not email:
            continue
        yield {
            "email": email,
            "membership_id": snap.id,
            "firstname": data.get("name"),
            "lastname": data.get("surname"),
            "phone": data.get("phone"),
            "birthdate": data.get("birthdate"),
        }


def iter_participants_with_consent(
    limit: Optional[int] = None,
    batch_size: int = 200,
    single_shot: bool = False,
):
    """
    Reads newsletter consent rows directly from `newsletter_consents`.
    Yields only active entries (active != False).
    """
    stream = _paged_stream(
        db.collection("newsletter_consents"),
        limit=limit,
        batch_size=batch_size,
        offset=0,
        single_shot=single_shot,
    )
    fetched = 0
    for doc in stream:
        data = doc.to_dict() or {}
        if data.get("active") is False:
            continue
        email = normalize_email(data.get("email"))
        if not email:
            continue
        yield {
            "email": email,
            "participant_id": data.get("participant_id") or doc.id,
            "event_id": data.get("event_id", ""),
            "firstname": data.get("name"),
            "lastname": data.get("surname"),
            "phone": data.get("phone"),
            "birthdate": data.get("birthdate"),
            "gender": data.get("gender"),
        }
        fetched += 1
        if limit is not None and fetched >= limit:
            return


# ------------------------------------------------------------------ #
# main
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="Bootstrap Sender from Firestore data.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to Sender.")
    parser.add_argument("--limit", type=int, default=None, help="Limit records per collection.")
    parser.add_argument("--batch-size", type=int, default=200, help="Firestore batch size.")
    parser.add_argument("--single-shot", action="store_true", help="Read collections in a single query stream (no batching).")
    parser.add_argument("--no-phone", action="store_true", help="Never send phone field to Sender.")
    parser.add_argument("--memberships-offset", type=int, default=0, help="Skip first N memberships.")
    parser.add_argument("--skip-memberships", action="store_true", help="Skip memberships phase.")
    parser.add_argument("--skip-participants", action="store_true", help="Skip participants phase.")
    args = parser.parse_args()

    svc = SenderService()
    group_cache: Dict[str, str] = {}  # title.lower() -> group_id
    email_cache: Dict[str, bool] = {}  # email -> already upserted
    event_cache: Dict[str, str] = {}  # event_id -> title

    # ── Phase 1: Memberships ─────────────────────────────────────── #
    if not args.skip_memberships:
        print("\n=== Phase 1: Memberships → group 'Memberships' ===")
        memberships_group_id = _find_or_create_group(svc, "Memberships", group_cache, args.dry_run)
        if not memberships_group_id:
            print("[memberships] ERROR: could not get/create Memberships group. Skipping phase.")
        else:
            if args.memberships_offset:
                print(f"[memberships] skipping first {args.memberships_offset}")
            progress = Progress("memberships", total=args.limit)
            for item in iter_memberships(
                limit=args.limit,
                offset=args.memberships_offset,
                batch_size=args.batch_size,
                single_shot=args.single_shot,
            ):
                _upsert(
                    svc=svc,
                    email=item["email"],
                    firstname=item.get("firstname"),
                    lastname=item.get("lastname"),
                    phone=item.get("phone"),
                    group_ids=[memberships_group_id],
                    dry_run=args.dry_run,
                    email_cache=email_cache,
                    no_phone=args.no_phone,
                )
                progress.update()
            progress.done()

    # ── Phase 2: Newsletter consents ──────────────────────────────── #
    if not args.skip_participants:
        print("\n=== Phase 2: Newsletter consents (active=True) → 'Newsletter' + 'Participant-{title}' ===")
        newsletter_group_id = _find_or_create_group(svc, "Newsletter", group_cache, args.dry_run)
        if not newsletter_group_id:
            print("[consents] ERROR: could not get/create Newsletter group. Skipping phase.")
        else:
            progress = Progress("consents", total=args.limit)
            for item in iter_participants_with_consent(
                limit=args.limit,
                batch_size=args.batch_size,
                single_shot=args.single_shot,
            ):
                event_id = item.get("event_id", "")
                event_title = _get_event_title(event_id, event_cache) if event_id else ""

                group_ids = [newsletter_group_id]
                if event_title:
                    per_event_group_id = _find_or_create_group(
                        svc, f"Participant-{event_title}", group_cache, args.dry_run
                    )
                    if per_event_group_id:
                        group_ids.append(per_event_group_id)
                else:
                    print(f"\n[consents] WARNING: no event title for event_id={event_id}, skipping per-event group")

                _upsert(
                    svc=svc,
                    email=item["email"],
                    firstname=item.get("firstname"),
                    lastname=item.get("lastname"),
                    phone=item.get("phone"),
                    group_ids=group_ids,
                    dry_run=args.dry_run,
                    email_cache=email_cache,
                    no_phone=args.no_phone,
                )
                progress.update()
            progress.done()

    now = datetime.now(timezone.utc).isoformat()
    print(f"\n[done] {now}")
    print(f"[summary] upserted={len(email_cache)} subscribers, events cached={len(event_cache)}, groups={list(group_cache.keys())}")


if __name__ == "__main__":
    main()
