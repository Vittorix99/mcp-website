from dataclasses import dataclass

from .base import FirestoreModel


@dataclass
class EventLocation(FirestoreModel):
    """Location document stored in the ``event_locations`` collection."""
    label: str = ""
    maps_url: str = ""
    maps_embed_url: str = ""
    address: str = ""
    message: str = ""
    published: bool = False
