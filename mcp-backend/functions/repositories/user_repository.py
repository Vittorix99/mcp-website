from typing import Optional, Dict

from config.firebase_config import db


class UserRepository:
    def __init__(self):
        self.collection = db.collection("users")

    def get_by_id(self, user_id: str) -> Optional[Dict]:
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            return None
        return doc.to_dict() or {}
