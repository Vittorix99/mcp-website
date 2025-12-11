from typing import Dict, Optional

from models import Membership

from dto import MembershipDTO
from repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership, MembershipDTO]):
    def __init__(self):
        super().__init__("memberships", Membership, MembershipDTO)

    def update_with_protected_check(self, membership_id: str, payload: Dict[str, Optional[str]], protected_fields=None) -> bool:
        protected_fields = protected_fields or []
        if any(field in payload for field in protected_fields):
            raise ValueError("Protected fields cannot be updated")
        self.update(membership_id, payload)
        return True
