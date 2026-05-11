from typing import Optional

from models.event_guide import EventGuide
from repositories.base import BaseRepository


class EventGuideRepository(BaseRepository[EventGuide]):
    def __init__(self):
        super().__init__("event_guides", EventGuide)

    def get(self, event_id: str) -> Optional[EventGuide]:
        return self.get_by_id(event_id)

    def replace(self, event_id: str, guide: EventGuide) -> None:
        """Full replace (no merge) — overwrites the entire document."""
        self.collection.document(event_id).set(guide.to_firestore(include_none=True))

    def set_published(self, event_id: str, published: bool) -> None:
        self.collection.document(event_id).set({"published": published}, merge=True)
