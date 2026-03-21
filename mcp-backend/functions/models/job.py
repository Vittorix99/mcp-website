from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class Job(FirestoreModel):
    """Represents a background job stored in the jobs collection."""

    type: str = ""
    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "event_id"})
    status: str = "queued"
    address: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    total: int = 0
    sent: int = 0
    failed: int = 0
    percent: int = 0
    created_at: Optional[Any] = None
    error: Optional[str] = None
