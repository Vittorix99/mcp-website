from __future__ import annotations

from typing import Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, Union

from google.cloud import firestore

from config.firebase_config import db

Model = TypeVar("Model")
DTO = TypeVar("DTO")


class BaseRepository(Generic[Model, DTO]):
    """
    Shared Firestore persistence helpers that convert between models and DTOs.
    """

    def __init__(self, collection_name: str, model_cls: Type[Model], dto_cls: Type[DTO]):
        self.collection_name = collection_name
        self.model_cls = model_cls
        self.dto_cls = dto_cls
        self.collection = db.collection(collection_name)

    def _model_from_snapshot(self, snapshot: firestore.DocumentSnapshot) -> Model:
        return self.model_cls.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def _dto_from_model(self, model: Model) -> DTO:
        return self.dto_cls.from_model(model)

    def _dict_from_model(self, model: Model) -> Dict[str, Any]:
        return model.to_firestore(include_none=True)

    def _normalize_payload(self, payload: Union[Dict[str, Any], DTO]) -> Dict[str, Any]:
        if hasattr(payload, "to_payload"):
            return payload.to_payload()
        return payload  # type: ignore[return-value]

    def get_all(self) -> List[DTO]:
        snapshots = self.collection.stream()
        result: List[DTO] = []
        for snapshot in snapshots:
            model = self._model_from_snapshot(snapshot)
            result.append(self._dto_from_model(model))
        return result

    def get_by_id(self, identifier: str) -> Optional[DTO]:
        doc = self.collection.document(identifier).get()
        if not doc.exists:
            return None
        model = self._model_from_snapshot(doc)
        return self._dto_from_model(model)

    def create(self, payload: Union[Dict[str, Any], DTO]) -> str:
        normalized = self._normalize_payload(payload)
        ref = self.collection.add(normalized)[1]
        return ref.id

    def update(self, identifier: str, payload: Union[Dict[str, Any], DTO]) -> bool:
        normalized = self._normalize_payload(payload)
        doc_ref = self.collection.document(identifier)
        doc_ref.set(normalized, merge=True)
        return True

    def delete(self, identifier: str) -> None:
        self.collection.document(identifier).delete()

    def stream(self) -> Iterable[DTO]:
        for snapshot in self.collection.stream():
            model = self._model_from_snapshot(snapshot)
            yield self._dto_from_model(model)
