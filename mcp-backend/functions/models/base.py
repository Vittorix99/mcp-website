from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict, Optional


@dataclass
class FirestoreModel:
    """
    Lightweight base class used by the backend refactor to describe Firestore
    documents as Python dataclasses. Each field can provide the original
    Firestore key through ``metadata={"firestore_name": "camelCaseKey"}``.
    """

    id: Optional[str] = field(default=None, metadata={"firestore_name": None})

    def to_firestore(self, include_none: bool = False) -> Dict[str, Any]:
        """
        Convert the dataclass instance into a Firestore-friendly dictionary.
        Enum values are stored as their raw value. ``None`` values are skipped
        unless ``include_none`` is True.
        """
        payload: Dict[str, Any] = {}
        for f in fields(self):
            if f.name == "id":
                continue
            key = f.metadata.get("firestore_name", f.name)
            value = getattr(self, f.name)

            if value is None and not include_none:
                continue

            enum_cls = f.metadata.get("enum")
            if enum_cls and isinstance(value, Enum):
                value = value.value

            payload[key] = value
        return payload

    @classmethod
    def from_firestore(cls, data: Dict[str, Any], doc_id: Optional[str] = None):
        """
        Build the dataclass from a Firestore dictionary. Enum fields are
        reconstructed automatically if the metadata declares ``enum``.
        """
        kwargs: Dict[str, Any] = {"id": doc_id}
        for f in fields(cls):
            if f.name == "id":
                continue
            key = f.metadata.get("firestore_name", f.name)
            if key not in data:
                continue
            value = data[key]
            enum_cls = f.metadata.get("enum")
            if enum_cls and value is not None:
                try:
                    value = enum_cls(value)
                except ValueError:
                    continue
            kwargs[f.name] = value
        return cls(**kwargs)
