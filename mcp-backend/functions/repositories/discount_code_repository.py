from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
from google.cloud.firestore_v1 import transactional as _fs_transactional

from config.firebase_config import db
from errors.service_errors import ConflictError, NotFoundError
from models import DiscountCode, DiscountType
from repositories.base import BaseRepository


class DiscountCodeRepository(BaseRepository[DiscountCode]):
    def __init__(self):
        super().__init__("discount_codes", DiscountCode)

    def _normalize_code(self, code: str) -> str:
        return (code or "").strip().upper()

    def _data_to_model(self, event_id: str, data: Dict[str, Any], admin_uid: str) -> DiscountCode:
        return DiscountCode(
            event_id=event_id,
            code=self._normalize_code(data.get("code")),
            discount_type=DiscountType(data.get("discount_type")),
            discount_value=float(data.get("discount_value")),
            max_uses=int(data.get("max_uses")),
            used_count=0,
            is_active=True,
            restricted_membership_id=data.get("restricted_membership_id"),
            restricted_email=(data.get("restricted_email") or None),
            created_at=firestore.SERVER_TIMESTAMP,
            created_by=admin_uid,
            updated_at=firestore.SERVER_TIMESTAMP,
            updated_by=admin_uid,
        )

    def create(self, event_id: str, data: Dict[str, Any], admin_uid: str) -> DiscountCode:
        code = self._normalize_code(data.get("code"))
        existing = (
            self.collection.where(filter=FieldFilter("event_id", "==", event_id))
            .where(filter=FieldFilter("code", "==", code))
            .limit(1)
            .get()
        )
        if existing:
            raise ConflictError("Codice già esistente per questo evento")

        ref = self.collection.document()
        model = self._data_to_model(event_id, {**data, "code": code}, admin_uid)
        ref.set(model.to_firestore(include_none=True))
        model.id = ref.id
        return model

    def get_by_id(self, discount_code_id: str) -> Optional[DiscountCode]:
        return super().get_by_id(discount_code_id)

    def get_by_code_and_event(self, code: str, event_id: str) -> Optional[DiscountCode]:
        matches = (
            self.collection.where(filter=FieldFilter("event_id", "==", event_id))
            .where(filter=FieldFilter("code", "==", self._normalize_code(code)))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def list_by_event(self, event_id: str) -> List[DiscountCode]:
        docs = (
            self.collection.where(filter=FieldFilter("event_id", "==", event_id))
            .stream()
        )
        models = [self._model_from_snapshot(doc) for doc in docs]
        return sorted(models, key=lambda item: str(item.created_at or ""))

    def update(self, discount_code_id: str, data: Dict[str, Any], admin_uid: str) -> DiscountCode:
        allowed = {
            "is_active": "isActive",
            "max_uses": "maxUses",
            "discount_value": "discountValue",
            "discount_type": "discountType",
            "restricted_membership_id": "restrictedMembershipId",
            "restricted_email": "restrictedEmail",
        }
        payload: Dict[str, Any] = {}
        for key, firestore_key in allowed.items():
            if key not in data:
                continue
            value = data[key]
            if key == "discount_type" and value is not None:
                value = DiscountType(value).value
            payload[firestore_key] = value

        if not payload:
            raise ValueError("No update fields provided")

        payload["updatedAt"] = firestore.SERVER_TIMESTAMP
        payload["updatedBy"] = admin_uid
        doc_ref = self.collection.document(discount_code_id)
        if not doc_ref.get().exists:
            raise NotFoundError("Codice sconto non trovato")
        doc_ref.update(payload)
        updated = self.get_by_id(discount_code_id)
        if not updated:
            raise NotFoundError("Codice sconto non trovato")
        return updated

    def increment_used_count(self, discount_code_id: str, transaction=None) -> None:
        doc_ref = self.collection.document(discount_code_id)
        payload = {"usedCount": firestore.Increment(1), "updatedAt": firestore.SERVER_TIMESTAMP}
        if transaction is not None:
            transaction.update(doc_ref, payload)
            return
        doc_ref.update(payload)

    def claim_usage(self, discount_code_id: str) -> None:
        doc_ref = self.collection.document(discount_code_id)

        @_fs_transactional
        def _claim(transaction):
            snapshot = doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                raise NotFoundError("Codice sconto non trovato")
            data = snapshot.to_dict() or {}
            used_count = int(data.get("usedCount") or 0)
            max_uses = int(data.get("maxUses") or 0)
            if used_count >= max_uses:
                raise ConflictError("Codice sconto esaurito, riprova senza codice sconto")
            self.increment_used_count(discount_code_id, transaction=transaction)

        _claim(db.transaction())
