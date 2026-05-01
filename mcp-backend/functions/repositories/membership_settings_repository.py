from typing import Optional

from config.firebase_config import db


class MembershipSettingsRepository:
    def __init__(self):
        self.collection = db.collection("membership_settings")

    def get_price_by_year(self, year: str) -> Optional[float]:
        doc = self.collection.document("price").get()
        if not doc.exists:
            return None
        payload = doc.to_dict() or {}
        price_by_year = payload.get("price_by_year", {}) or {}
        fee = price_by_year.get(year)
        try:
            return float(fee) if fee is not None else None
        except (TypeError, ValueError):
            return None

    def set_price_by_year(self, year: str, price: float) -> None:
        self.collection.document("price").set(
            {"price_by_year": {year: price}},
            merge=True,
        )

    def get_wallet_model(self) -> Optional[str]:
        doc = self.collection.document("current_model").get()
        if not doc.exists:
            return None
        payload = doc.to_dict() or {}
        model_id = payload.get("model_id")
        return str(model_id).strip() if model_id else None

    def set_wallet_model(self, model_id: str) -> None:
        self.collection.document("current_model").set({"model_id": model_id}, merge=True)
