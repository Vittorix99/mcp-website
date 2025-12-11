from typing import Dict, Optional

from models import Event

from dto import EventDTO
from repositories.base import BaseRepository


class EventRepository(BaseRepository[Event, EventDTO]):
    def __init__(self):
        super().__init__("events", Event, EventDTO)

    def upsert(self, event_id: str, payload: Dict[str, Optional[str]]) -> str:
        """
        Create or update a single event. Returns the event ID.
        """
        if event_id:
            self.collection.document(event_id).set(payload, merge=True)
            return event_id
        return self.create(payload)
