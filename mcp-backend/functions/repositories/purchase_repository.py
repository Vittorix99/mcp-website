from typing import Iterable, Optional
from hashlib import sha256
from decimal import Decimal, InvalidOperation
from datetime import datetime

from google.api_core.exceptions import AlreadyExists
from errors.service_errors import ConflictError

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

    def find_by_order(self, order_id: str) -> Optional[Purchase]:
        docs = self.collection.where(filter=FieldFilter("order_id", "==", order_id)).limit(2).get()
        if len(docs) > 1:
            raise ConflictError("Multiple purchases for order: manual verification required")
        return self._model_from_snapshot(docs[0]) if docs else None

    @staticmethod
    def assert_same_checkout(existing: Purchase, expected: EventPurchase) -> None:
        fields = ("order_id", "transaction_id", "currency", "status", "capture_status",
                  "ref_id", "event_id", "discount_code_id", "event_purchase_type", "payment_method")
        if any(getattr(existing, field, None) != getattr(expected, field, None) for field in fields):
            raise ConflictError("Purchase does not match captured order")
        for field in ("payer_name", "payer_surname", "payer_email"):
            if str(getattr(existing, field) or "").strip().casefold() != str(getattr(expected, field) or "").strip().casefold():
                raise ConflictError("Purchase payer does not match captured order")
        def instant(value):
            if value is None or value == "":
                return None
            result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if result.tzinfo is None:
                raise ValueError("Missing capture timezone")
            return result
        try:
            if instant(existing.timestamp) != instant(expected.timestamp):
                raise ConflictError("Purchase timestamp does not match captured order")
        except (TypeError, ValueError) as exc:
            raise ConflictError("Invalid existing purchase timestamp") from exc
        try:
            for field in ("amount_total", "paypal_fee", "net_amount", "discount_amount"):
                actual = Decimal(str(getattr(existing, field, None) or 0))
                wanted = Decimal(str(getattr(expected, field, None) or 0))
                if not actual.is_finite() or actual != wanted:
                    raise ConflictError("Purchase amount does not match captured order")
        except InvalidOperation as exc:
            raise ConflictError("Invalid existing purchase amount") from exc

    def create_for_order(self, purchase: EventPurchase) -> str:
        existing = self.find_by_order(purchase.order_id)
        if existing:
            self.assert_same_checkout(existing, purchase)
            return existing.id
        ref = self.collection.document("checkout-" + sha256(purchase.order_id.encode()).hexdigest())
        purchase.slug = build_slug(purchase.payer_name, purchase.payer_surname, suffix=ref.id[-6:])
        try:
            ref.create(purchase.to_firestore(include_none=True))
        except AlreadyExists:
            existing = self._model_from_snapshot(ref.get())
            self.assert_same_checkout(existing, purchase)
            return existing.id
        return ref.id

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

    def update_status(self, purchase_id: str, status: str) -> None:
        self.collection.document(purchase_id).update({"status": status})

    def delete(self, purchase_id: str) -> bool:
        doc_ref = self.collection.document(purchase_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True
