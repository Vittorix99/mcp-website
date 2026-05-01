from typing import Optional

from config.firebase_config import db
from models import UserProfile


class UserRepository:
    def __init__(self):
        self.collection = db.collection("users")

    def get_by_id(self, user_id: str) -> Optional[UserProfile]:
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            return None
        return UserProfile.from_firestore(doc.to_dict() or {}, doc.id)
