from typing import Any, Dict, Optional

from config.firebase_config import db
from models import EventOrder


class OrderRepository:
    def __init__(self):
        self.collection = db.collection("orders")

    def save(self, order_id: str, order: EventOrder) -> None:
        self.collection.document(order_id).set(order.to_firestore(include_none=True))

    def get(self, order_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.document(order_id).get()
        if not doc.exists:
            return None
        return doc.to_dict() or {}

    def delete(self, order_id: str) -> None:
        self.collection.document(order_id).delete()

    def update_status(self, order_id: str, status: str) -> None:
        self.collection.document(order_id).update({"orderStatus": status})
