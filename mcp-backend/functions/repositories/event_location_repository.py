from typing import Optional

from models.event_location import EventLocation
from repositories.base import BaseRepository


class EventLocationRepository(BaseRepository[EventLocation]):
    def __init__(self):
        super().__init__("event_locations", EventLocation)

    def get(self, event_id: str) -> Optional[EventLocation]:
        return self.get_by_id(event_id)

    def upsert_all(self, event_id: str, location: EventLocation) -> None:
        """Full replace of all location fields from the admin Posizione tab."""
        self.collection.document(event_id).set(
            {
                "label": location.label,
                "maps_url": location.maps_url,
                "maps_embed_url": location.maps_embed_url,
                "address": location.address,
                "message": location.message,
            },
            merge=True,
        )

    def set_published(self, event_id: str, published: bool) -> None:
        self.collection.document(event_id).set({"published": published}, merge=True)

    def merge_public_fields(self, event_id: str, location: EventLocation) -> None:
        """Write public guide fields (label, maps_url, maps_embed_url) without overwriting address."""
        self.collection.document(event_id).set(
            {
                "label": location.label,
                "maps_url": location.maps_url,
                "maps_embed_url": location.maps_embed_url,
            },
            merge=True,
        )

    def merge_address(self, event_id: str, address: str, maps_url: str) -> None:
        """Write the precise address (from send_location) without overwriting other fields."""
        self.collection.document(event_id).set(
            {"address": address, "maps_url": maps_url},
            merge=True,
        )
