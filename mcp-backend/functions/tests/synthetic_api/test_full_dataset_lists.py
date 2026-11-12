"""OPS-10: full synthetic corpus list reads through the real admin handlers."""
import os
import time
from datetime import date

from flask import Flask, request

from api.admin import events_api, members_api, participants_api, purchases_api
from config.firebase_config import db
from tests.synthetic_api.conftest import _loader as loader
from tests.synthetic_api.test_seed_resume import generator


def _image():
    paths = sorted(loader._document_paths(db))
    result = {}
    for offset in range(0, len(paths), 400):
        refs = [db.document(path) for path in paths[offset:offset + 400]]
        result.update({snap.reference.path: snap.to_dict() for snap in db.get_all(refs)})
    return result


def _ids(rows):
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    return set(ids)


def _route(app, path, handler, method):
    def invoke():
        return handler(request)
    app.add_url_rule(path, path, invoke, methods=[method])


def test_full_dataset_admin_lists_match_export(tmp_path, monkeypatch):
    dataset = generator.generate(seed=42, as_of=date(2026, 11, 12), email_base="owner@example.com")
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    output = tmp_path / ".local/staging/full"
    generator.write_export(dataset, output)
    records, manifest = loader.read_export(output)
    assert manifest["members"] == 4000 and manifest["events"] == 50

    loader.load(records, project="demo-mcp-test", host=os.environ["FIRESTORE_EMULATOR_HOST"],
                hub=os.environ["FIREBASE_EMULATOR_HUB"])
    expected_image = {row["path"]: row["data"] for row in records}
    assert _image() == expected_image

    members_raw = {row["path"].split("/", 1)[1]: row["data"] for row in records
                   if row["path"].startswith("memberships/")}
    events_raw = {row["path"].split("/", 1)[1]: row["data"] for row in records
                  if row["path"].startswith("events/")}
    purchases_raw = {row["path"].split("/", 1)[1]: row["data"] for row in records
                     if row["path"].startswith("purchases/")}
    participants_raw = {}
    for row in records:
        parts = row["path"].split("/")
        if len(parts) == 4 and parts[0] == "participants" and parts[2] == "participants_event":
            participants_raw.setdefault(parts[1], set()).add(parts[3])

    app = Flask("ops10-full-dataset-lists")
    _route(app, "/members", members_api.get_memberships, "GET")
    _route(app, "/events", events_api.admin_get_all_events, "GET")
    _route(app, "/participants", participants_api.get_participants_by_event, "POST")
    _route(app, "/purchases", purchases_api.get_all_purchases, "GET")
    app.config["TESTING"] = True
    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = "Bearer synthetic-test-admin"

    timings = {}

    def get_json(name, path, method="GET", body=None):
        started = time.perf_counter()
        response = client.open(path, method=method, json=body)
        elapsed = time.perf_counter() - started
        assert response.status_code == 200, response.get_data(as_text=True)[:500]
        timings[name] = timings.get(name, 0.0) + elapsed
        return response.get_json()

    all_members = get_json("members_all", "/members")
    assert len(all_members) == len(members_raw) == 4000
    assert _ids(all_members) == set(members_raw)
    members = get_json("members_2026", "/members?year=2026")
    expected_member_ids = {mid for mid, row in members_raw.items() if 2026 in row["membership_years"]}
    assert len(members) == len(expected_member_ids)
    assert _ids(members) == expected_member_ids
    members_2025 = get_json("members_2025", "/members?year=2025")
    expected_2025 = {mid for mid, row in members_raw.items() if 2025 in row["membership_years"]}
    assert len(members_2025) == len(expected_2025) and _ids(members_2025) == expected_2025
    members_2030 = get_json("members_missing_year", "/members?year=2030")
    assert members_2030 == []

    events = get_json("events", "/events")
    assert len(events) == len(events_raw) == 50
    assert _ids(events) == set(events_raw)
    for event in events:
        assert event["participantsCount"] == len(participants_raw.get(event["id"], set()))

    purchases = get_json("purchases", "/purchases")
    assert len(purchases) == len(purchases_raw)
    assert _ids(purchases) == set(purchases_raw)
    expected_purchase_events = {pid: row.get("event_id") or row.get("ref_id")
                                for pid, row in purchases_raw.items()}
    actual_purchase_events = {row["id"]: row.get("eventId") or row.get("event_id") or row.get("refId") or row.get("ref_id")
                              for row in purchases}
    assert actual_purchase_events == expected_purchase_events

    participant_total = 0
    for event_id in events_raw:
        participants = get_json("participant_reads_total_seconds", "/participants", method="POST",
                                body={"eventId": event_id})
        expected_ids = participants_raw.get(event_id, set())
        assert len(participants) == len(expected_ids)
        assert _ids(participants) == expected_ids
        participant_total += len(participants)

    assert participant_total == manifest["expected"]["global"]["participants"]
    assert _image() == expected_image
    print({"scenario": "ops10_full_dataset_lists", "members": len(members_raw),
           "events": len(events), "purchases": len(purchases), "participants": participant_total,
           "seconds": timings})
