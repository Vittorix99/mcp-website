from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .base import FirestoreModel


@dataclass
class ErrorLog(FirestoreModel):
    """Represents an external-service failure stored in Firestore."""

    service: str = ""
    operation: Optional[str] = None
    source: Optional[str] = None
    message: str = ""
    status_code: Optional[int] = field(default=None, metadata={"firestore_name": "status_code"})
    payload: Optional[Any] = None
    context: Optional[Dict[str, Any]] = None
    severity: str = "error"
    resolved: bool = False
    created_at: Optional[str] = field(default=None, metadata={"firestore_name": "created_at"})
    updated_at: Optional[str] = field(default=None, metadata={"firestore_name": "updated_at"})
