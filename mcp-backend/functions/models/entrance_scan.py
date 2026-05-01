from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class EntranceScan(FirestoreModel):
    """Represents a recorded entrance scan stored in ``entrance_scans/{event_id}/scans``."""

    scanned_at: Optional[Any] = field(default=None, metadata={"firestore_name": "scanned_at"})
    scan_token: Optional[str] = field(default=None, metadata={"firestore_name": "scan_token"})
    manual: bool = field(default=False, metadata={"firestore_name": "manual"})
    operator: Optional[str] = field(default=None, metadata={"firestore_name": "operator"})
