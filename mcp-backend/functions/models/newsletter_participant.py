from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .base import FirestoreModel


@dataclass
class NewsletterParticipant(FirestoreModel):
    """Participant imported into the newsletter flow, preserving request extras."""

    email: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[Any] = None

    def to_firestore(self, include_none: bool = False) -> Dict[str, Any]:
        payload = dict(self.extra or {})
        payload["email"] = self.email
        if self.timestamp is not None or include_none:
            payload["timestamp"] = self.timestamp
        return payload

    @classmethod
    def from_firestore(cls, data: Dict[str, Any], doc_id: Optional[str] = None):
        payload = dict(data or {})
        email = payload.pop("email", "") or ""
        timestamp = payload.pop("timestamp", None)
        return cls(id=doc_id, email=email, extra=payload, timestamp=timestamp)
