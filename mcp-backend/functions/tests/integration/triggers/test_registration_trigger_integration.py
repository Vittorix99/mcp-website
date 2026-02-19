import importlib
import os
import socket
import time
import urllib.request
from uuid import uuid4

import pytest


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _ensure_emulators():
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        if _is_port_open("127.0.0.1", 8080):
            os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
        elif _is_port_open("localhost", 8080):
            os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.skip("Firestore emulator is not active")

    if not _is_port_open("127.0.0.1", 5002) and not _is_port_open("localhost", 5002):
        pytest.skip("Functions emulator is not active on port 5002")

    if not _is_port_open("127.0.0.1", 8085) and not _is_port_open("localhost", 8085):
        pytest.skip("Pub/Sub emulator is not active on port 8085")


def _fetch_functions_yaml() -> str | None:
    for port in (5002, 8081):
        for host in ("127.0.0.1", "localhost"):
            url = f"http://{host}:{port}/__/functions.yaml"
            try:
                with urllib.request.urlopen(url, timeout=0.5) as resp:
                    if resp.status == 200:
                        return resp.read().decode("utf-8", errors="ignore")
            except Exception:
                continue
    return None


def _assert_trigger_registered(trigger_name: str) -> None:
    yaml_text = _fetch_functions_yaml()
    if not yaml_text:
        return
    if trigger_name not in yaml_text:
        pytest.skip(f"Functions emulator did not load trigger '{trigger_name}'")


def _load_firebase_config():
    _ensure_emulators()
    import firebase_admin
    import config.firebase_config as firebase_config

    for app in list(firebase_admin._apps.values()):
        firebase_admin.delete_app(app)

    return importlib.reload(firebase_config)


def _assert_firestore_emulator(firebase_config):
    host = os.environ.get("FIRESTORE_EMULATOR_HOST")
    emulator_host = getattr(firebase_config.db, "_emulator_host", None)
    if not host or not emulator_host:
        pytest.fail(
            "Firestore emulator is not configured on the client. "
            f"FIRESTORE_EMULATOR_HOST={host!r}, db._emulator_host={emulator_host!r}"
        )


def _wait_for(predicate, timeout: float = 8.0, interval: float = 0.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


@pytest.mark.integration
def test_on_participant_created_updates_firestore(monkeypatch):
    firebase_config = _load_firebase_config()
    _assert_firestore_emulator(firebase_config)
    _assert_trigger_registered("on_participant_created")
    db = firebase_config.db
    event_id = f"evt_{uuid4().hex[:8]}"
    participant_id = f"part_{uuid4().hex[:8]}"
    ref = (
        db.collection("participants")
        .document(event_id)
        .collection("participants_event")
        .document(participant_id)
    )
    ref.set(
        {
            "name": "Andrea",
            "email": "invalid",
            "send_ticket_on_create": False,
            "newsletterConsent": False,
        }
    )
    try:
        assert _wait_for(lambda: (ref.get().to_dict() or {}).get("gender") == "male")
        updated = ref.get().to_dict() or {}
        assert updated.get("gender_probability") == 1.0
    finally:
        ref.delete()


@pytest.mark.integration
def test_on_membership_created_generates_card():
    firebase_config = _load_firebase_config()
    _assert_firestore_emulator(firebase_config)
    _assert_trigger_registered("on_membership_created")
    db = firebase_config.db
    bucket = firebase_config.bucket

    if bucket is None:
        pytest.skip("Storage bucket not configured for trigger test")

    membership_id = f"mem_{uuid4().hex[:8]}"
    ref = db.collection("memberships").document(membership_id)
    ref.set(
        {
            "name": "Mario",
            "surname": "Rossi",
            "email": "invalid",
            "subscription_valid": True,
            "send_card_on_create": False,
        }
    )

    storage_path = None
    try:
        assert _wait_for(lambda: bool((ref.get().to_dict() or {}).get("card_url")))
        updated = ref.get().to_dict() or {}
        storage_path = updated.get("card_storage_path")
        assert storage_path
    finally:
        if storage_path and bucket is not None:
            blob = bucket.blob(storage_path)
            if blob.exists():
                blob.delete()
        ref.delete()
