# services/admin/purchases_service.py

import logging
from flask import jsonify
from firebase_admin import firestore
from config.firebase_config import db

class PurchasesService:
    def __init__(self):
        self.db = db
        self.collection = db.collection("purchases")
        self.logger = logging.getLogger("PurchasesService")

    def get_all(self):
        try:
            docs = self.collection.stream()
            purchases = [doc.to_dict() | {"id": doc.id} for doc in docs]
            return jsonify(purchases), 200
        except Exception as e:
            self.logger.error(f"[get_all] {e}")
            return {"error": str(e)}, 500

    def get_by_id(self, purchase_id):
        try:
            doc = self.collection.document(purchase_id).get()
            if not doc.exists:
                return {"error": "Purchase not found"}, 404
            return jsonify(doc.to_dict() | {"id": doc.id}), 200
        except Exception as e:
            self.logger.error(f"[get_by_id] {e}")
            return {"error": str(e)}, 500

    def create(self, data):
        try:
            required_fields = [
                "payer_name", "payer_surname", "payer_email",
                "amount_total", "currency", "transaction_id", "order_id", "timestamp", "type"
            ]
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return {"error": f"Missing fields: {', '.join(missing_fields)}"}, 400

            purchase = {
                "payer_name": data["payer_name"],
                "payer_surname": data["payer_surname"],
                "payer_email": data["payer_email"],
                "amount_total": data["amount_total"],
                "currency": data["currency"],
                "paypal_fee": data.get("paypal_fee"),
                "net_amount": data.get("net_amount"),
                "transaction_id": data["transaction_id"],
                "order_id": data["order_id"],
                "status": data.get("status", "COMPLETED"),
                "timestamp": data["timestamp"],
                "type": data["type"],
                "ref_id": data.get("ref_id"),  # può essere None
            }

            ref = self.collection.add(purchase)[1]
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