from typing import Any, Dict, Iterable, List, Optional, Union

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from dto import MembershipDTO
from models import Membership
from repositories.base import BaseRepository
from utils.slug_utils import build_slug


class MembershipRepository(BaseRepository[Membership, MembershipDTO]):
    def __init__(self):
        super().__init__("memberships", Membership, MembershipDTO)

    def get(self, membership_id: str) -> Optional[Membership]:
        if not membership_id:
            return None
        doc = self.collection.document(membership_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    # Backward compatibility for existing callers.
    def get_model(self, membership_id: str) -> Optional[Membership]:
        return self.get(membership_id)

    def list(self) -> List[Membership]:
        return [self._model_from_snapshot(doc) for doc in self.collection.stream()]

    def get_last_by_start_date(self) -> Optional[MembershipDTO]:
        docs = (
            self.collection
            .order_by("start_date", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        model = self._model_from_snapshot(docs[0])
        return MembershipDTO.from_model(model)

    def get_model_by_slug(self, slug: str) -> Optional[Membership]:
        if not slug:
            return None
        matches = self.collection.where("slug", "==", slug).limit(1).get()
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def update_with_protected_check(self, membership_id: str, payload: Dict[str, Optional[str]], protected_fields=None) -> bool:
        protected_fields = protected_fields or []
        if any(field in payload for field in protected_fields):
            raise ValueError("Protected fields cannot be updated")
        self.update(membership_id, payload)
        return True

    def find_by_email(self, email: str) -> Optional[Membership]:
        if not email:
            return None
        docs = self.collection.where("email", "==", email).limit(1).get()
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def find_by_phone(self, phone: str) -> Optional[Membership]:
        if not phone:
            return None
        docs = self.collection.where("phone", "==", phone).limit(1).get()
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def create(self, payload: Union[Dict[str, Any], MembershipDTO, Membership]) -> str:
        if isinstance(payload, Membership):
            return self.create_from_model(payload)
        return super().create(payload)

    def create_from_model(self, membership: Membership) -> str:
        ref = self.collection.document()
        membership.slug = build_slug(membership.name, membership.surname, suffix=ref.id[-6:])
        ref.set(membership.to_firestore(include_none=True))
        return ref.id

    def update_fields(self, membership_id: str, payload: Dict[str, Any]) -> bool:
        self.collection.document(membership_id).update(payload)
        return True

    def append_purchase(self, membership_id: str, purchase_id: str) -> bool:
        if not membership_id or not purchase_id:
            return False
        self.collection.document(membership_id).update(
            {"purchases": firestore.ArrayUnion([purchase_id])}
        )
        return True

    def add_attended_event_and_purchase(
        self, membership_id: str, event_id: str, purchase_id: str
    ) -> bool:
        if not membership_id or not event_id or not purchase_id:
            return False
        self.collection.document(membership_id).update(
            {
                "attended_events": firestore.ArrayUnion([event_id]),
                "purchases": firestore.ArrayUnion([purchase_id]),
            }
        )
        return True

    def add_attended_event(self, membership_id: str, event_id: str) -> bool:
        if not membership_id or not event_id:
            return False
        self.collection.document(membership_id).update(
            {"attended_events": firestore.ArrayUnion([event_id])}
        )
        return True

    def add_renewal(self, membership_id: str, renewal_dict: Dict[str, Any]) -> bool:
        if not membership_id or not isinstance(renewal_dict, dict):
            return False

        year = renewal_dict.get("year")
        try:
            year = int(year) if year is not None else None
        except (TypeError, ValueError):
            year = None

        membership = self.get(membership_id)
        if not membership:
            return False

        existing_years = set(membership.membership_years or [])
        if year is not None and year in existing_years:
            return True

        updates: Dict[str, Any] = {
            "renewals": firestore.ArrayUnion([renewal_dict]),
        }
        if year is not None:
            updates["membership_years"] = firestore.ArrayUnion([year])
        self.collection.document(membership_id).update(updates)
        return True

    def find_by_year(self, year: int) -> List[Membership]:
        docs = self.collection.where("membership_years", "array_contains", int(year)).stream()
        return [self._model_from_snapshot(doc) for doc in docs]

    def update_from_model(self, membership_id: str, payload: Union[Membership, MembershipDTO]) -> bool:
        if isinstance(payload, MembershipDTO):
            update_payload = payload.to_update_payload()
            if not update_payload:
                return True
            self.collection.document(membership_id).update(update_payload)
            return True
        self.collection.document(membership_id).set(payload.to_firestore(include_none=True), merge=True)
        return True

    def list_by_purchase_ids(self, purchase_ids: List[str]) -> Iterable[Membership]:
        if not purchase_ids:
            return []
        snaps = (
            self.collection
            .where(filter=FieldFilter("purchase_id", "in", purchase_ids))
            .stream()
        )
        for snap in snaps:
            yield self._model_from_snapshot(snap)

    def clear_wallet(self, membership_id: str) -> None:
        self.collection.document(membership_id).update({
            "wallet_pass_id": None,
            "wallet_url": None,
        })

    def set_wallet(self, membership_id: str, pass_id: str, wallet_url: str) -> None:
        self.collection.document(membership_id).update({
            "wallet_pass_id": pass_id,
            "wallet_url": wallet_url,
        })

    def set_merging(self, membership_id: str, value: Optional[bool]) -> None:
        self.collection.document(membership_id).update({"merging": value})

    def list_by_ids(self, membership_ids: List[str]) -> Iterable[Membership]:
        if not membership_ids:
            return []
        doc_refs = [self.collection.document(member_id) for member_id in membership_ids]
        snaps = (
            self.collection
            .where(filter=FieldFilter("__name__", "in", doc_refs))
            .stream()
        )
        for snap in snaps:
            yield self._model_from_snapshot(snap)
