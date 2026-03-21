from typing import Dict, Optional, Iterable, Any

from google.cloud.firestore_v1 import FieldFilter

from models import Event

from dto import EventDTO
from repositories.base import BaseRepository
from utils.slug_utils import build_slug


class EventRepository(BaseRepository[Event, EventDTO]):
    def __init__(self):
        super().__init__("events", Event, EventDTO)

    def stream_models(self) -> Iterable[Event]:
        for snapshot in self.collection.stream():
            yield self._model_from_snapshot(snapshot)

    def get_model(self, event_id: str) -> Optional[Event]:
        doc = self.collection.document(event_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def get_model_by_slug(self, slug: str) -> Optional[Event]:
        matches = (
            self.collection.where(filter=FieldFilter("slug", "==", slug))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def get_payload_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        matches = (
            self.collection.where(filter=FieldFilter("slug", "==", slug))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        doc = matches[0]
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    def upsert(self, event_id: str, payload: Dict[str, Optional[str]]) -> str:
        """
        Create or update a single event. Returns the event ID.
        """
        if event_id:
            self.collection.document(event_id).set(payload, merge=True)
            return event_id
        return self.create(payload)

    def get_payload(self, event_id: str) -> Optional[Dict]:
        doc = self.collection.document(event_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["id"] = event_id
        return data

    def get_raw_type(self, event_id: str) -> Optional[str]:
        doc = self.collection.document(event_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        raw_type = data.get("type")
        return str(raw_type) if raw_type is not None else None

    def create_from_model(self, event: Event, slug_seed: str) -> str:
        ref = self.collection.document()
        event.slug = build_slug(slug_seed, suffix=ref.id[-6:])
        ref.set(event.to_firestore(include_none=True))
        return ref.id

    def update_from_model(self, event_id: str, event: Event) -> None:
        self.collection.document(event_id).set(event.to_firestore(include_none=True), merge=True)

    def update_fields(self, event_id: str, payload: Dict[str, Any]) -> None:
        self.collection.document(event_id).update(payload)
