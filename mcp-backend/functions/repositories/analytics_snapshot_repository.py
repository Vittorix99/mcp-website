from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

from config.firebase_config import db


class AnalyticsSnapshotRepository:
    def __init__(self):
        self.dashboard_collection = db.collection("analytics_dashboard")
        self.event_collection = db.collection("analytics_event")
        self.global_collection = db.collection("analytics_global")

    def get_dashboard_current(self) -> Optional[Dict[str, Any]]:
        doc = self.dashboard_collection.document("current").get()
        if not doc.exists:
            return None
        payload = doc.to_dict() or {}
        payload["id"] = doc.id
        return payload

    def set_dashboard_current(self, payload: Dict[str, Any]) -> None:
        self.dashboard_collection.document("current").set(payload, merge=True)

    def get_global_current(self) -> Optional[Dict[str, Any]]:
        doc = self.global_collection.document("current").get()
        if not doc.exists:
            return None
        payload = doc.to_dict() or {}
        payload["id"] = doc.id
        return payload

    def set_global_current(self, payload: Dict[str, Any]) -> None:
        self.global_collection.document("current").set(payload, merge=True)

    def get_event_snapshot(self, event_id: str) -> Optional[Dict[str, Any]]:
        doc = self.event_collection.document(event_id).get()
        if not doc.exists:
            return None
        payload = doc.to_dict() or {}
        payload["id"] = doc.id
        return payload

    def set_event_snapshot(self, event_id: str, payload: Dict[str, Any]) -> None:
        self.event_collection.document(event_id).set(payload, merge=True)

    def stream_event_snapshots(self) -> Iterable[Tuple[str, Dict[str, Any]]]:
        for doc in self.event_collection.stream():
            yield doc.id, (doc.to_dict() or {})
