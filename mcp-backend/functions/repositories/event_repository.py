from __future__ import annotations

from typing import Iterable, Optional

from google.cloud.firestore_v1 import FieldFilter

from models import Event
from repositories.base import BaseRepository
from utils.slug_utils import build_slug


class EventRepository(BaseRepository[Event]):
    def __init__(self):
        super().__init__("events", Event)

    def stream_models(self) -> Iterable[Event]:
        return self.stream()

    def get_model(self, event_id: str) -> Optional[Event]:
        if not event_id:
            return None
        return self.get_by_id(event_id)

    def get_model_by_slug(self, slug: str) -> Optional[Event]:
        if not slug:
            return None
        matches = (
            self.collection.where(filter=FieldFilter("slug", "==", slug))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def create_from_model(self, event: Event, slug_seed: str) -> str:
        ref = self.collection.document()
        event.slug = build_slug(slug_seed, suffix=ref.id[-6:])
        ref.set(event.to_firestore(include_none=True)) ## This will create the document with the generated ID, which is needed to ensure slug uniqueness.
        return ref.id
    
    


    def update_from_model(self, event_id: str, event: Event) -> None:
        self.collection.document(event_id).set(event.to_firestore(include_none=True), merge=True)

    def delete(self, event_id: str) -> None:
        self.collection.document(event_id).delete()
