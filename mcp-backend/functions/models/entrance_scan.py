from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class EntranceScan(FirestoreModel):
    """Represents a recorded entrance scan stored in ``entrance_scans/{event_id}/scans``."""

    scanned_at: Optional[Any] = field(default=None, metadata={"firestore_name": "scanned_at"})
    scan_token: str = field(default="", metadata={"firestore_name": "scan_token"})
