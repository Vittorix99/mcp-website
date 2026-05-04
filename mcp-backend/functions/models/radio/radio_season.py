from dataclasses import dataclass, field
from typing import Any, Optional

from models.base import FirestoreModel


@dataclass
class RadioSeason(FirestoreModel):
    """Represents a radio season document in the ``radio_seasons`` collection."""

    name: str = ""
    year: int = 0
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})
    updated_at: Optional[Any] = field(default=None, metadata={"firestore_name": "updatedAt"})
