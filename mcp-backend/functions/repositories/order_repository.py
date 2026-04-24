from typing import Any, Dict, Optional

from google.cloud import firestore
from config.firebase_config import db
from models import EventOrder


class OrderRepository:
    def __init__(self):
        self.collection = db.collection("orders")

    def save(self, order_id: str, order: EventOrder) -> None:
        data = order.to_firestore(include_none=True)
        data["created_at"] = firestore.SERVER_TIMESTAMP
        self.collection.document(order_id).set(data)

    def get(self, order_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.document(order_id).get()
        if not doc.exists:
            return None
        return doc.to_dict() or {}

    def delete(self, order_id: str) -> None:
        self.collection.document(order_id).delete()

    def update_status(self, order_id: str, status: str) -> None:
        self.collection.document(order_id).update({"orderStatus": status})

    def update_fields(self, order_id: str, fields: Dict[str, Any]) -> None:
        self.collection.document(order_id).update(fields)

    def mark_captured(self, order_id: str, payment_method: str) -> None:
        self.collection.document(order_id).update({
            "captured": True,
            "payment_method": payment_method,
        })

    def set_purchase_id(self, order_id: str, purchase_id: str) -> None:
        self.collection.document(order_id).update({"purchase_id": purchase_id})
