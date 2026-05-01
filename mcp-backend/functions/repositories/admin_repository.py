from typing import List, Optional

from models import AdminUser
from repositories.base import BaseRepository


class AdminRepository(BaseRepository[AdminUser]):
    def __init__(self):
        super().__init__("admin_users", AdminUser)

    def list_models(self) -> List[AdminUser]:
        return self.get_all()

    def get(self, admin_id: str) -> Optional[AdminUser]:
        if not admin_id:
            return None
        return self.get_by_id(admin_id)

    def create_with_id(self, admin_id: str, admin_user: AdminUser) -> None:
        self.collection.document(admin_id).set(admin_user.to_firestore(include_none=True))

    def update_from_model(self, admin_id: str, admin_user: AdminUser) -> None:
        self.collection.document(admin_id).set(admin_user.to_firestore(include_none=True), merge=True)

    def delete(self, admin_id: str) -> None:
        self.collection.document(admin_id).delete()
