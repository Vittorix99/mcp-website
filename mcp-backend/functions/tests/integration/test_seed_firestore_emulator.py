import importlib
import os
import socket
import time
from uuid import uuid4

import pytest


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _ensure_firestore_emulator():
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        if _is_port_open("127.0.0.1", 8080):
            os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
        elif _is_port_open("localhost", 8080):
            os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.skip("Firestore emulator is not active")


def _load_firebase_config():
    _ensure_firestore_emulator()
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


@pytest.mark.integration
def test_seed_firestore_emulator_data():
    """Seeds Firestore emulator with sample data (no cleanup)."""
    firebase_config = _load_firebase_config()
    _assert_firestore_emulator(firebase_config)
    db = firebase_config.db

    seed_id = f"seed_{uuid4().hex[:8]}"
    payload = {
        "seed": True,
        "source": "pytest",
        "created_at": time.time(),
        "note": "Intentional seed record for emulator (no cleanup).",
    }
    db.collection("seed_samples").document(seed_id).set(payload)

    stored = db.collection("seed_samples").document(seed_id).get().to_dict() or {}
    assert stored.get("seed") is True
