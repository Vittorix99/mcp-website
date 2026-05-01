from dataclasses import dataclass, field

from .base import FirestoreModel


@dataclass
class UserProfile(FirestoreModel):
    is_admin: bool = field(default=False, metadata={"firestore_name": "isAdmin"})
    role: str = "user"
