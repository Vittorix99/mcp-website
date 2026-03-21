"""
Seed Sender with test subscribers in a target group using plus addressing.

Default behavior:
  - group: "Test group"
  - count: 20
  - base email: mcpweb.test@gmail.com
  - generated emails: mcpweb.test+sender_test_01@gmail.com, ...

Usage:
  python scripts/sender_seed_test_group.py
  python scripts/sender_seed_test_group.py --count 20 --group "Test group"
  python scripts/sender_seed_test_group.py --dry-run
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency in some local shells
    def load_dotenv(*args, **kwargs):
        return False

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load local env used by functions.
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path, override=False)

from services.sender.sender_service import SenderService  # noqa: E402


def split_email(email: str) -> Tuple[str, str]:
    value = (email or "").strip().lower()
    if "@" not in value:
        raise ValueError(f"Invalid base email: {email}")
    local, domain = value.split("@", 1)
    if not local or not domain:
        raise ValueError(f"Invalid base email: {email}")
    return local, domain


def plus_email(base_email: str, prefix: str, index: int) -> str:
    local, domain = split_email(base_email)
    safe_prefix = (prefix or "sender_test").strip().replace(" ", "_").lower()
    return f"{local}+{safe_prefix}_{index:02d}@{domain}"


def extract_groups(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload, list):
        return payload
    return []


def find_or_create_group(svc: SenderService, title: str, dry_run: bool = False) -> Optional[str]:
    if dry_run:
        return "dry-run-group-id"

    groups_payload = svc.list_groups()
    for group in extract_groups(groups_payload):
        if str(group.get("title", "")).strip().lower() == title.strip().lower():
            return str(group.get("id"))

    created = svc.create_group(title)
    if not isinstance(created, dict):
        return None
    data = created.get("data") if isinstance(created.get("data"), dict) else created
    group_id = data.get("id")
    return str(group_id) if group_id else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Sender test subscribers into one group.")
    parser.add_argument("--group", default="Test group", help="Target Sender group title.")
    parser.add_argument("--count", type=int, default=20, help="Number of subscribers to generate.")
    parser.add_argument(
        "--base-email",
        default=os.environ.get("MAILERLITE_TEST_EMAIL_BASE", "mcpweb.test@gmail.com"),
        help="Base email used for plus addressing (e.g. mcpweb.test@gmail.com).",
    )
    parser.add_argument("--prefix", default="sender_test", help="Plus addressing prefix.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without calling Sender.")
    args = parser.parse_args()

    if args.count <= 0:
        print("count must be > 0")
        return 1

    try:
        split_email(args.base_email)
    except ValueError as exc:
        print(str(exc))
        return 1

    svc = SenderService()

    try:
        group_id = find_or_create_group(svc, args.group, dry_run=args.dry_run)
    except Exception as exc:
        print(f"[error] unable to list/create group '{args.group}': {exc}")
        return 1

    if not group_id:
        print(f"[error] group '{args.group}' not found/created")
        return 1

    print(f"[info] target group: {args.group} (id={group_id})")
    print(f"[info] generating {args.count} subscriber(s) from base={args.base_email}")

    created = 0
    failed = 0
    for idx in range(1, args.count + 1):
        email = plus_email(args.base_email, args.prefix, idx)
        firstname = "MCP"
        lastname = f"Test {idx:02d}"

        if args.dry_run:
            print(f"[dry-run] upsert {email} -> group={args.group}")
            created += 1
            continue

        result = svc.upsert_subscriber(
            email=email,
            firstname=firstname,
            lastname=lastname,
            groups=[group_id],
        )
        if result is None:
            print(f"[warn] failed upsert for {email}")
            failed += 1
            continue

        # Ensure assignment even if provider ignores group IDs in upsert payload.
        svc.add_to_group(email, group_id)
        print(f"[ok] {email}")
        created += 1

    now = datetime.now(timezone.utc).isoformat()
    print(f"[done] {now}")
    print(f"[summary] success={created} failed={failed} group='{args.group}'")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
