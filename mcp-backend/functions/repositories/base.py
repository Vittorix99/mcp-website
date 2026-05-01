from __future__ import annotations

from typing import Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar

from google.cloud import firestore

from config.firebase_config import db

Model = TypeVar("Model")


class BaseRepository(Generic[Model]):
    """Helper Firestore condiviso per repository che lavorano su una singola collection."""

    def __init__(self, collection_name: str, model_cls: Type[Model]):
        self.collection_name = collection_name
        self.model_cls = model_cls
        self.collection = db.collection(collection_name)

    def _model_from_snapshot(self, snapshot: firestore.DocumentSnapshot) -> Model:
        return self.model_cls.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def _dict_from_model(self, model: Model) -> Dict[str, Any]:
        return model.to_firestore(include_none=True)

    def get_all(self) -> List[Model]:
        return [self._model_from_snapshot(snap) for snap in self.collection.stream()]

    def get_by_id(self, identifier: str) -> Optional[Model]:
        doc = self.collection.document(identifier).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def create(self, model: Model) -> str:
        ref = self.collection.add(self._dict_from_model(model))[1]
        return ref.id

    def update(self, identifier: str, model: Model) -> bool:
        doc_ref = self.collection.document(identifier)
        doc_ref.set(self._dict_from_model(model), merge=True)
        return True

    def delete(self, identifier: str) -> None:
        self.collection.document(identifier).delete()

    def stream(self) -> Iterable[Model]:
        for snapshot in self.collection.stream():
            yield self._model_from_snapshot(snapshot)
