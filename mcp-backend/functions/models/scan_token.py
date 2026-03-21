from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class ScanToken(FirestoreModel):
    """Represents a scanner session token stored in ``scan_tokens``."""

    event_id: str = field(default="", metadata={"firestore_name": "event_id"})
    created_by: str = field(default="", metadata={"firestore_name": "created_by"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "created_at"})
    expires_at: Optional[Any] = field(default=None, metadata={"firestore_name": "expires_at"})
    is_active: bool = field(default=True, metadata={"firestore_name": "is_active"})
