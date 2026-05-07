from typing import Iterable, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from models import EventPurchase, Purchase, PurchaseTypes
from utils.slug_utils import build_slug


class PurchaseRepository:
    def __init__(self):
        self.collection = db.collection("purchases")

    _EVENT_TYPE_VALUES = {PurchaseTypes.EVENT.value, "event_and_membership"}

    def _model_from_snapshot(self, snapshot) -> Purchase:
        data = snapshot.to_dict() or {}
        purchase_type = data.get("type")
        if purchase_type in self._EVENT_TYPE_VALUES:
            return EventPurchase.from_firestore(data, snapshot.id)
        return Purchase.from_firestore(data, snapshot.id)

    def create(self, purchase: Purchase) -> str:
        ref = self.collection.document()
        purchase.slug = build_slug(purchase.payer_name, purchase.payer_surname, suffix=ref.id[-6:])
        ref.set(purchase.to_firestore(include_none=True))
        return ref.id

    def create_from_model(self, purchase: Purchase) -> str:
        return self.create(purchase)

    def update_participants(self, purchase_id: str, participants_count: int, membership_ids: list[str]) -> None:
        payload = {
            "participants_count": participants_count,
            "membership_ids": membership_ids,
        }
        self.collection.document(purchase_id).update(payload)

    def stream_models(self) -> Iterable[Purchase]:
        for snap in self.collection.stream():
            yield self._model_from_snapshot(snap)

    def get_model(self, purchase_id: str) -> Optional[Purchase]:
        doc = self.collection.document(purchase_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def get_model_by_slug(self, slug: str) -> Optional[Purchase]:
        matches = (
            self.collection.where(filter=FieldFilter("slug", "==", slug))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def get_last_by_timestamp(self) -> Optional[Purchase]:
        docs = (
            self.collection
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        doc = docs[0]
        return self._model_from_snapshot(doc)

    def list_models_by_ref_id(self, event_id: str) -> Iterable[Purchase]:
        snaps = (
            self.collection
            .where(filter=FieldFilter("ref_id", "==", event_id))
            .stream()
        )
        for snap in snaps:
            yield self._model_from_snapshot(snap)

    def delete(self, purchase_id: str) -> bool:
        doc_ref = self.collection.document(purchase_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True
