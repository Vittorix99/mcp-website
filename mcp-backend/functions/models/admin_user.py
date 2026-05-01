from dataclasses import dataclass, field
from typing import Any, Optional

from .base import FirestoreModel


@dataclass
class AdminUser(FirestoreModel):
    email: str = ""
    display_name: str = field(default="", metadata={"firestore_name": "displayName"})
    created_at: Optional[Any] = field(default=None, metadata={"firestore_name": "createdAt"})
    created_by: Optional[str] = field(default=None, metadata={"firestore_name": "createdBy"})
