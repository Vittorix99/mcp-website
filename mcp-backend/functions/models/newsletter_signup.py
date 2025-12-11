from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class NewsletterSignup(FirestoreModel):
    """Represents a single entry inside ``newsletter_signups``."""

    email: str = ""
    timestamp: Optional[Any] = None
    active: bool = True
    source: Optional[str] = field(default=None, metadata={"firestore_name": "source"})
