import os
import socket
import time


def test_purchase_write_enqueues_analytics_job():
    from config.firebase_config import db
    hostname, port = os.environ["FIRESTORE_EMULATOR_HOST"].split(":")
    with socket.create_connection((hostname,int(port)),timeout=2):
        pass
    purchase = db.collection("purchases").document("smoke-purchase")
    purchase.set({"ref_id":"smoke-event","status":"COMPLETED"})
    found = []
    try:
        deadline = time.monotonic()+20
        while time.monotonic() < deadline:
            found = [document for document in db.collection("analytics_jobs").stream()
                     if (document.to_dict() or {}).get("target_event_id") == "smoke-event"]
            if found:
                break
            time.sleep(.2)
        assert found, "Firestore purchase trigger did not enqueue analytics job"
    finally:
        purchase.delete()
        for document in found:
            document.reference.delete()
