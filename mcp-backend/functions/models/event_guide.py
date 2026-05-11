from dataclasses import dataclass, field
from typing import Any, List

from .base import FirestoreModel


@dataclass
class EventGuide(FirestoreModel):
    """Guide document stored in the ``event_guides`` collection."""
    published: bool = False
    sections: List[Any] = field(default_factory=list)
