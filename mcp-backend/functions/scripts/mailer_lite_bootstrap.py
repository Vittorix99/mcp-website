import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from pathlib import Path
from itertools import cycle
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI0IiwianRpIjoiMWMxMzIxMTUyMzUwMDk4Y2FkNDQ3ZWM1Y2YyMDdkNWI2ZTg2NTlmYjQ1NDViN2E4NjBmNmUwYjVlYzYxNmQ4NGNlZjFmNjBlNjU0OGY0YTkiLCJpYXQiOjE3NzA4Mzg3NDkuOTM3NjU3LCJuYmYiOjE3NzA4Mzg3NDkuOTM3NjYsImV4cCI6NDkyNjUxMjM0OS45MzE3NTMsInN1YiI6IjIxMTMyODUiLCJzY29wZXMiOltdfQ.FXP-LW3o8gwCuEWbmQT6xrLyFxUvhnCeu0finRChk2Mey7ZXkP_JR2KWs_-MNjbRgNYwZq-sLk5VDnCjxvMX1daHqxm2d4Im8DnHP_VVUsBBHVJlFtMs-nUKGQl6o2atQiq6OrT9iQfUkW7HM2GBVDoVLd9JVMeP4PrN81g1eMIdjCKYc2I5B9-GMnBeWh3fTI_70Jd3EkwW1Rc6Vvvp_Bwr0aV9ncJXrJQpnMA-o0XmXmfrz-4F9Vq6DgaijKUCQ24_GWPk11vqGmPlzcIpL3tcW1HsZt7MVTmQXmv_6P3K23YVabSzko1I6FduOflrODhErvUgFA9cC7719hM4uNw9Z37XydNC1gEsPZCEl7lDJ1lDntjHs6C3mT3OMy6XwNmnbH9ZfQmUVQR8o9EyXSdEMQAoJSJNR-kr8vm9VYqjccebSEhn8-G5nG8n1w3UD9fvgi6UxJoxLuXc6qUN1zbacDy2cX0n7UUiA8Nwbmx0yWrRXVnIA-es5kuu4XQmWbizWOWgv2NG95-PUk7ymgLgLlVpYNiXfa6RIB90_CJ5FVc6JTmVgySB0padbzWIngV3R9OLEemXdzmAkQYvQf7BmoZfAl2WAGrZAK2IKkvsnpSKCmltwMHZuDAEaZHtF4jrRpKcEJDlWtahZbDVnnqJPIJbKNCq2e_5xQ95YH4"

from config.firebase_config import db
from services.mailer_lite import (
    FieldsClient,
    GroupsClient,
    SubscribersClient,
    MailerLiteClient,
    MailerLiteSubscribersRegistry,
)
from utils.events_utils import normalize_email


GROUP_MEMBERSHIPS = "memberships"
GROUP_NEWSLETTER = "newsletter"

CUSTOM_FIELDS = [
    {"name": "phone", "type": "text"},
    {"name": "birthdate", "type": "text"},
    {"name": "gender", "type": "text"},
    {"name": "membership_id", "type": "text"},
    {"name": "participant_id", "type": "text"},
]

SEGMENTS = [
    {"name": "Subscriber nuovi", "definition": None},
    {"name": "Subscriber con più di 6 mesi con noi", "definition": None},
    {"name": "Subscriber con età inferiore ai 22 anni", "definition": None},
    {"name": "Subscribers con età inferiore ai 22 anni", "definition": None},
]


def _paged_stream(
    collection,
    limit: Optional[int] = None,
    batch_size: int = 200,
    offset: int = 0,
):
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


def _extract_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("id", "subscriber_id", "subscriberId"):
                if key in data:
                    return str(data[key])
        for key in ("id", "subscriber_id", "subscriberId"):
            if key in payload:
                return str(payload[key])
    return None


def _extract_group_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and "id" in data:
            return str(data["id"])
        if "id" in payload:
            return str(payload["id"])
    return None


def _extract_group_name(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and "name" in data:
            return data["name"]
        if "name" in payload:
            return payload["name"]
    return None


def _list_all_fields(fields_client: FieldsClient, limit: int = 100) -> List[dict]:
    page = 1
    results = []
    while True:
        response = fields_client.list(params={"limit": limit, "page": page})
        data = response.get("data") if isinstance(response, dict) else None
        if not data:
            break
        results.extend(data)
        meta = response.get("meta") if isinstance(response, dict) else None
        if not meta:
            break
        current = meta.get("current_page")
        last_page = meta.get("last_page")
        if current and last_page and current >= last_page:
            break
        page += 1
    return results


def _extract_field_name(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and "name" in data:
            return data["name"]
        if "name" in payload:
            return payload["name"]
    return None


def ensure_custom_fields(fields_client: FieldsClient, fields: List[Dict[str, str]], dry_run: bool):
    existing = set()
    for item in _list_all_fields(fields_client):
        name = _extract_field_name(item)
        if name:
            existing.add(name)

    for entry in fields:
        name = entry.get("name")
        field_type = entry.get("type", "text")
        if not name or name in existing:
            continue
        if dry_run:
            print(f"[fields] create '{name}' type={field_type} (dry-run)")
            continue
        try:
            fields_client.create(name, field_type)
            print(f"[fields] created '{name}' ({field_type})")
        except Exception as e:
            print(f"[fields] create failed '{name}': {e}")

def _list_all_groups(groups_client: GroupsClient, limit: int = 100) -> List[dict]:
    page = 1
    results = []
    while True:
        response = groups_client.list(params={"limit": limit, "page": page})
        data = response.get("data") if isinstance(response, dict) else None
        if not data:
            break
        results.extend(data)
        meta = response.get("meta") if isinstance(response, dict) else None
        if not meta:
            break
        current = meta.get("current_page")
        last_page = meta.get("last_page")
        if current and last_page and current >= last_page:
            break
        page += 1
    return results


def ensure_groups(groups_client: GroupsClient, group_names: List[str], dry_run: bool) -> Dict[str, str]:
    existing = {}
    for item in _list_all_groups(groups_client):
        name = _extract_group_name(item)
        group_id = _extract_group_id(item)
        if name and group_id:
            existing[name] = group_id

    mapping = dict(existing)
    for name in group_names:
        if name in mapping:
            continue
        if dry_run:
            print(f"[groups] create '{name}' (dry-run)")
            continue
        response = groups_client.create(name)
        group_id = _extract_group_id(response)
        if not group_id:
            print(f"[groups] unable to read id for '{name}', response={response}")
            continue
        mapping[name] = group_id
        print(f"[groups] created '{name}' -> {group_id}")
    return mapping


def _get_or_create_subscriber(
    subscribers_client: SubscribersClient,
    registry: MailerLiteSubscribersRegistry,
    email: str,
    fields: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    cache: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    normalized = normalize_email(email)
    if not normalized:
        return None

    if cache is not None and normalized in cache:
        return cache[normalized]

    cached = registry.get(normalized)
    if cached and cached.get("mailerlite_id"):
        subscriber_id = str(cached.get("mailerlite_id"))
        if cache is not None:
            cache[normalized] = subscriber_id
        return subscriber_id

    if dry_run:
        print(f"[subscribers] ensure {normalized} (dry-run)")
        if cache is not None:
            cache[normalized] = "dry-run"
        return "dry-run"

    subscriber_id = None
    try:
        response = subscribers_client.get(normalized)
        subscriber_id = _extract_id(response)
    except Exception:
        subscriber_id = None

    if not subscriber_id:
        try:
            response = subscribers_client.create(normalized, {"fields": fields} if fields else {})
            subscriber_id = _extract_id(response)
        except Exception as e:
            print(f"[subscribers] create failed for {normalized}: {e}")
            try:
                response = subscribers_client.get(normalized)
                subscriber_id = _extract_id(response)
            except Exception as e2:
                print(f"[subscribers] get failed for {normalized}: {e2}")
                subscriber_id = None

    if subscriber_id:
        try:
            registry.upsert(normalized, subscriber_id)
        except Exception as e:
            print(f"[registry] unable to store {normalized}: {e}")
        if cache is not None:
            cache[normalized] = subscriber_id
    return subscriber_id


def _assign_to_group(
    groups_client: GroupsClient,
    subscriber_id: Optional[str],
    group_id: Optional[str],
    dry_run: bool = False,
):
    if not subscriber_id or not group_id:
        return
    if dry_run:
        print(f"[groups] assign subscriber {subscriber_id} -> group {group_id} (dry-run)")
        return
    try:
        groups_client.assign_subscriber(subscriber_id, group_id)
    except Exception as e:
        print(f"[groups] assign failed subscriber={subscriber_id} group={group_id}: {e}")


def iter_memberships(limit: Optional[int] = None, offset: int = 0, batch_size: int = 200):
    stream = _paged_stream(
        db.collection("memberships"),
        limit=limit,
        batch_size=batch_size,
        offset=offset,
    )
    for snap in stream:
        data = snap.to_dict() or {}
        email = normalize_email(data.get("email"))
        if not email:
            continue
        yield {
            "email": email,
            "membership_id": snap.id,
            "name": data.get("name"),
            "last_name": data.get("surname"),
            "phone": data.get("phone"),
            "birthdate": data.get("birthdate"),
            "start_date": data.get("start_date"),
        }


def iter_newsletter_consents(limit: Optional[int] = None, offset: int = 0, batch_size: int = 200):
    stream = _paged_stream(
        db.collection("newsletter_consents"),
        limit=limit,
        batch_size=batch_size,
        offset=offset,
    )
    for snap in stream:
        data = snap.to_dict() or {}
        email = normalize_email(data.get("email"))
        if not email:
            continue
        yield {
            "email": email,
            "name": data.get("name"),
            "last_name": data.get("surname"),
            "phone": data.get("phone"),
            "birthdate": data.get("birthdate"),
            "gender": data.get("gender"),
            "participant_id": data.get("participant_id"),
            "event_id": data.get("event_id"),
            "timestamp": data.get("timestamp"),
        }


def format_mailerlite_datetime(value: Any) -> Optional[str]:
    if not value:
        return None
    dt = None
    if hasattr(value, "to_datetime"):
        try:
            dt = value.to_datetime()
        except Exception:
            dt = None
    if dt is None:
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                dt = None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_segments(client: MailerLiteClient, segments: List[Dict[str, Any]], dry_run: bool):
    sdk_segments = getattr(client.sdk, "segments", None)
    if not sdk_segments or not hasattr(sdk_segments, "create"):
        print("[segments] SDK does not expose create(). Skipping segment creation.")
        return

    for segment in segments:
        name = segment.get("name")
        definition = segment.get("definition")
        if not name:
            continue
        if dry_run:
            print(f"[segments] create '{name}' (dry-run) definition={definition}")
            continue
        try:
            if definition:
                sdk_segments.create(definition)
            else:
                sdk_segments.create({"name": name})
            print(f"[segments] created '{name}'")
        except Exception as e:
            print(f"[segments] create failed '{name}': {e}")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap MailerLite from Firestore data.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to MailerLite.")
    parser.add_argument("--limit", type=int, default=None, help="Limit records per collection.")
    parser.add_argument("--batch-size", type=int, default=200, help="Firestore batch size.")
    parser.add_argument("--memberships-offset", type=int, default=0, help="Skip first N memberships.")
    parser.add_argument("--consents-offset", type=int, default=0, help="Skip first N newsletter consents.")
    parser.add_argument("--skip-memberships", action="store_true", help="Skip memberships.")
    parser.add_argument("--skip-consents", action="store_true", help="Skip newsletter consents.")
    parser.add_argument("--skip-segments", action="store_true", help="Skip segments.")

    args = parser.parse_args()

    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    fields_client = FieldsClient()
    groups_client = GroupsClient()
    subscribers_client = SubscribersClient()
    registry = MailerLiteSubscribersRegistry()

    ensure_custom_fields(fields_client, CUSTOM_FIELDS, args.dry_run)

    group_map = ensure_groups(
        groups_client,
        [GROUP_MEMBERSHIPS, GROUP_NEWSLETTER],
        dry_run=args.dry_run,
    )
    cache = {}

    if not args.skip_memberships:
        group_id = group_map.get(GROUP_MEMBERSHIPS)
        label = "memberships"
        if args.memberships_offset:
            print(f"[memberships] skipping first {args.memberships_offset}")
        progress = Progress(label, total=args.limit)
        for item in iter_memberships(
            limit=args.limit,
            offset=args.memberships_offset,
            batch_size=args.batch_size,
        ):
            fields = {
                "name": item.get("name"),
                "last_name": item.get("last_name"),
                "phone": item.get("phone"),
                "birthdate": item.get("birthdate"),
                "membership_id": item.get("membership_id"),
            }
            subscribed_at = format_mailerlite_datetime(item.get("start_date"))
            subscriber_id = _get_or_create_subscriber(
                subscribers_client,
                registry,
                item["email"],
                fields=fields,
                dry_run=args.dry_run,
                cache=cache,
            )
            if subscribed_at and not args.dry_run:
                try:
                    subscribers_client.update(item["email"], {"subscribed_at": subscribed_at})
                except Exception as e:
                    print(f"[subscribers] subscribed_at update failed for {item['email']}: {e}")
            _assign_to_group(groups_client, subscriber_id, group_id, dry_run=args.dry_run)
            progress.update()
        progress.done()

    if not args.skip_consents:
        group_id = group_map.get(GROUP_NEWSLETTER)
        label = "newsletter_consents"
        if args.consents_offset:
            print(f"[newsletter_consents] skipping first {args.consents_offset}")
        progress = Progress(label, total=args.limit)
        for item in iter_newsletter_consents(
            limit=args.limit,
            offset=args.consents_offset,
            batch_size=args.batch_size,
        ):
            fields = {
                "name": item.get("name"),
                "last_name": item.get("last_name"),
                "phone": item.get("phone"),
                "birthdate": item.get("birthdate"),
                "gender": item.get("gender"),
                "participant_id": item.get("participant_id"),
            }
            opted_in_at = format_mailerlite_datetime(item.get("timestamp"))
            subscribed_at = format_mailerlite_datetime(item.get("timestamp"))
            subscriber_id = _get_or_create_subscriber(
                subscribers_client,
                registry,
                item["email"],
                fields=fields,
                dry_run=args.dry_run,
                cache=cache,
            )
            if (opted_in_at or subscribed_at) and not args.dry_run:
                try:
                    update_payload = {}
                    if opted_in_at:
                        update_payload["opted_in_at"] = opted_in_at
                    if subscribed_at:
                        update_payload["subscribed_at"] = subscribed_at
                    subscribers_client.update(item["email"], update_payload)
                except Exception as e:
                    print(f"[subscribers] subscribed_at update failed for {item['email']}: {e}")
            _assign_to_group(groups_client, subscriber_id, group_id, dry_run=args.dry_run)
            progress.update()
        progress.done()

    if not args.skip_segments:
        create_segments(MailerLiteClient(api_key=API_KEY), SEGMENTS, args.dry_run)

    now = datetime.now(timezone.utc).isoformat()
    print(f"[done] {now}")


if __name__ == "__main__":
    main()
