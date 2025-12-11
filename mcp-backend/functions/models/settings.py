from dataclasses import dataclass, field
from typing import Any, Dict

from .base import FirestoreModel


@dataclass
class Setting(FirestoreModel):
    """
    Represents a simple key/value configuration entry stored inside the
    ``settings`` collection (document id acts as the key).
    """

    key: str = field(default="", metadata={"firestore_name": None})
    value: Any = None

    def to_firestore(self, include_none: bool = False) -> Dict[str, Any]:
        return {"value": self.value}

    @classmethod
    def from_firestore(cls, data: Dict[str, Any], doc_id=None):
        instance = super().from_firestore(data, doc_id=doc_id)
        instance.key = doc_id or ""
        return instance

    def to_kv(self) -> Dict[str, Any]:
        return {"key": self.key, "value": self.value}
