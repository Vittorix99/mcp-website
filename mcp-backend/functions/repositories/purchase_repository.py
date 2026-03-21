from typing import Dict, Iterable, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from models import Purchase
from utils.slug_utils import build_slug


class PurchaseRepository:
    def __init__(self):
        self.collection = db.collection("purchases")

    def create(self, purchase: Purchase) -> str:
        ref = self.collection.document()
        purchase.slug = build_slug(purchase.payer_name, purchase.payer_surname, suffix=ref.id[-6:])
        ref.set(purchase.to_firestore(include_none=True))
        return ref.id

    def create_from_model(self, purchase: Purchase) -> str:
        return self.create(purchase)

    def update_fields(self, purchase_id: str, payload: Dict) -> None:
        self.collection.document(purchase_id).update(payload)

    def update_participants(self, purchase_id: str, participants_count: int, membership_ids: list[str]) -> None:
        payload = {
            "participants_count": participants_count,
            "membership_ids": membership_ids,
        }
        self.collection.document(purchase_id).update(payload)

    def stream_models(self) -> Iterable[Purchase]:
        for snap in self.collection.stream():
            yield Purchase.from_firestore(snap.to_dict() or {}, snap.id)

    def get_model(self, purchase_id: str) -> Optional[Purchase]:
        doc = self.collection.document(purchase_id).get()
        if not doc.exists:
            return None
        return Purchase.from_firestore(doc.to_dict() or {}, doc.id)

    def get_model_by_slug(self, slug: str) -> Optional[Purchase]:
        matches = (
            self.collection.where(filter=FieldFilter("slug", "==", slug))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        return Purchase.from_firestore(matches[0].to_dict() or {}, matches[0].id)

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
        return Purchase.from_firestore(doc.to_dict() or {}, doc.id)

    def get(self, purchase_id: str) -> Optional[Dict]:
        doc = self.collection.document(purchase_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["id"] = purchase_id
        return data

    def list_by_ref_id(self, event_id: str) -> Iterable[Dict]:
        snaps = (
            self.collection
            .where(filter=FieldFilter("ref_id", "==", event_id))
            .stream()
        )
        for snap in snaps:
            data = snap.to_dict() or {}
            data["id"] = snap.id
            yield data

    def list_models_by_ref_id(self, event_id: str) -> Iterable[Purchase]:
        snaps = (
            self.collection
            .where(filter=FieldFilter("ref_id", "==", event_id))
            .stream()
        )
        for snap in snaps:
            yield Purchase.from_firestore(snap.to_dict() or {}, snap.id)

    def delete(self, purchase_id: str) -> bool:
        doc_ref = self.collection.document(purchase_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True
