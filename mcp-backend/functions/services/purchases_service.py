import logging
from typing import Dict

from flask import jsonify

from config.firebase_config import db
from models import Purchase


class PurchasesService:
    def __init__(self):
        self.db = db
        self.collection = db.collection("purchases")
        self.logger = logging.getLogger("PurchasesService")

    def _serialize(self, purchase: Purchase) -> Dict:
        payload = purchase.to_firestore(include_none=True)
        payload["id"] = purchase.id
        return payload

    def get_all(self):
        try:
            docs = self.collection.stream()
            purchases = [self._serialize(Purchase.from_firestore(doc.to_dict() or {}, doc.id)) for doc in docs]
            return jsonify(purchases), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {"error": str(e)}, 500

    def get_by_id(self, purchase_id):
        try:
            doc = self.collection.document(purchase_id).get()
            if not doc.exists:
                return {"error": "Purchase not found"}, 404
            purchase = Purchase.from_firestore(doc.to_dict() or {}, doc.id)
            return jsonify(self._serialize(purchase)), 200
        except Exception as e:
            self.logger.error(f"[get_by_id] {e}")
            return {"error": str(e)}, 500

    def create(self, data: Dict):
        try:
            required_fields = [
                "payer_name",
                "payer_surname",
                "payer_email",
                "amount_total",
                "currency",
                "transaction_id",
                "order_id",
                "timestamp",
                "type",
            ]
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return {"error": f"Missing fields: {', '.join(missing_fields)}"}, 400

            purchase = Purchase(
                payer_name=data["payer_name"],
                payer_surname=data["payer_surname"],
                payer_email=data["payer_email"],
                amount_total=data["amount_total"],
                currency=data["currency"],
                paypal_fee=data.get("paypal_fee"),
                net_amount=data.get("net_amount"),
                transaction_id=data["transaction_id"],
                order_id=data["order_id"],
                status=data.get("status", "COMPLETED"),
                timestamp=data["timestamp"],
                purchase_type=data.get("type"),
                ref_id=data.get("ref_id"),
            )

            ref = self.collection.add(purchase.to_firestore(include_none=True))[1]
            self.logger.info(f"[create] New purchase saved: {ref.id}")
            return jsonify({"message": "Purchase created", "id": ref.id}), 201

        except Exception as e:
            self.logger.error(f"[create] {e}")
            return {"error": str(e)}, 500

    def delete(self, purchase_id):
        try:
            doc_ref = self.collection.document(purchase_id)
            doc = doc_ref.get()
            if not doc.exists:
                return {"error": "Purchase not found"}, 404

            doc_ref.delete()
            self.logger.info(f"[delete] Purchase deleted: {purchase_id}")
            return jsonify({"message": "Purchase deleted"}), 200

        except Exception as e:
            self.logger.error(f"[delete] {e}")
            return {"error": str(e)}, 500
