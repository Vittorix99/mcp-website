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
