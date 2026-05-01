from typing import Optional

from google.cloud import firestore

from models import EventOrder
from repositories.base import BaseRepository


class OrderRepository(BaseRepository[EventOrder]):
    def __init__(self):
        super().__init__("orders", EventOrder)

    def save(self, order_id: str, order: EventOrder) -> None:
        data = order.to_firestore(include_none=True)
        data["createdAt"] = firestore.SERVER_TIMESTAMP
        self.collection.document(order_id).set(data)

    def get_model(self, order_id: str) -> Optional[EventOrder]:
        return self.get_by_id(order_id)

    def delete(self, order_id: str) -> None:
        self.collection.document(order_id).delete()

    def update_status(self, order_id: str, status: str) -> None:
        self.collection.document(order_id).update({"orderStatus": status})

    def mark_captured(self, order_id: str, payment_method: str) -> None:
        self.collection.document(order_id).update({
            "captured": True,
            "payment_method": payment_method,
        })

    def set_purchase_id(self, order_id: str, purchase_id: str) -> None:
        self.collection.document(order_id).update({"purchase_id": purchase_id})
