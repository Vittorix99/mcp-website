from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class Job(FirestoreModel):
    """Base lifecycle state for background jobs."""

    type: str = ""
    status: str = "queued"
    percent: int = 0
    created_at: Optional[Any] = None
    started_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    finished_at: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class LocationJob(Job):
    """Job payload for bulk location-email sending."""

    type: str = "send_location"
    event_id: Optional[str] = field(default=None, metadata={"firestore_name": "event_id"})
    address: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    total: int = 0
    sent: int = 0
    failed: int = 0


@dataclass
class AnalyticsJob(Job):
    """Job payload for analytics snapshot rebuilds."""

    type: str = "analytics_rebuild"
    target_event_id: Optional[str] = field(default=None, metadata={"firestore_name": "target_event_id"})
    scope: Optional[str] = None
    reason: Optional[str] = None
