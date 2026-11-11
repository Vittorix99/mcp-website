from typing import Optional

from google.cloud import firestore
from google.api_core.exceptions import Aborted, FailedPrecondition

from config.firebase_config import db
from errors.service_errors import ConflictError, NotFoundError
from models import EventOrder
from repositories.base import BaseRepository


_CLAIM_ATTEMPTS = 3


def _capture_conflict(order_id: str, data: dict) -> ConflictError:
    error = ConflictError("Order capture already claimed")
    error.payload = {
        "code": "ORDER_CAPTURE_CONFLICT",
        "order_id": order_id,
        "purchase_id": data.get("purchase_id"),
    }
    return error


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
        """Claim the capture exactly once; a concurrent or repeated claim raises ConflictError.

        Compare-and-set on the document's update time: no transaction locks, so
        simultaneous claims cannot deadlock. Only an unrelated change in between
        (e.g. a status update) is retried; a recorded capture is never overwritten.
        """
        doc_ref = self.collection.document(order_id)
        for _ in range(_CLAIM_ATTEMPTS):
            snapshot = doc_ref.get()
            if not snapshot.exists:
                raise NotFoundError("Order not found")
            data = snapshot.to_dict() or {}
            if data.get("captured"):
                raise _capture_conflict(order_id, data)
            try:
                doc_ref.update({
                    "captured": True,
                    "payment_method": payment_method,
                    "orderStatus": "PAYMENT_CAPTURED",
                }, option=db.write_option(last_update_time=snapshot.update_time))
                return
            except (FailedPrecondition, Aborted):
                continue
        error = ConflictError("Order changed concurrently, retry the capture")
        error.payload = {"code": "ORDER_CAPTURE_RETRY", "order_id": order_id}
        raise error

    def set_purchase_id(self, order_id: str, purchase_id: str) -> None:
        doc_ref = self.collection.document(order_id)
        for _ in range(_CLAIM_ATTEMPTS):
            snapshot = doc_ref.get()
            if not snapshot.exists:
                raise NotFoundError("Order not found")
            data = snapshot.to_dict() or {}
            if data.get("purchase_id"):
                if data["purchase_id"] != purchase_id:
                    raise ConflictError("Order already linked to a different purchase")
                return
            try:
                doc_ref.update({"purchase_id": purchase_id, "orderStatus": "PURCHASE_CREATED"},
                    option=db.write_option(last_update_time=snapshot.update_time))
                return
            except (FailedPrecondition, Aborted):
                continue
        raise ConflictError("Order changed concurrently, retry purchase linking")
