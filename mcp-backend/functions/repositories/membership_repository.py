from typing import Iterable, List, Optional

from google.cloud import firestore
from google.api_core.exceptions import Aborted, FailedPrecondition

from errors.service_errors import ConflictError, NotFoundError, ValidationError
from google.cloud.firestore_v1 import FieldFilter

from models import Membership
from repositories.base import BaseRepository
from utils.slug_utils import build_slug


class MembershipRepository(BaseRepository[Membership]):
    def __init__(self):
        super().__init__("memberships", Membership)

    def get(self, membership_id: str) -> Optional[Membership]:
        if not membership_id:
            return None
        doc = self.collection.document(membership_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def list(self) -> List[Membership]:
        return [self._model_from_snapshot(doc) for doc in self.collection.stream()]

    def get_last_by_start_date(self) -> Optional[Membership]:
        docs = (
            self.collection
            .order_by("start_date", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def get_model_by_slug(self, slug: str) -> Optional[Membership]:
        if not slug:
            return None
        matches = self.collection.where(filter=FieldFilter("slug", "==", slug)).limit(1).get()
        if not matches:
            return None
        return self._model_from_snapshot(matches[0])

    def find_by_email(self, email: str) -> Optional[Membership]:
        if not email:
            return None
        docs = self.collection.where(filter=FieldFilter("email", "==", email)).limit(1).get()
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def find_by_phone(self, phone: str) -> Optional[Membership]:
        if not phone:
            return None
        docs = self.collection.where(filter=FieldFilter("phone", "==", phone)).limit(1).get()
        if not docs:
            return None
        return self._model_from_snapshot(docs[0])

    def create(self, membership: Membership) -> str:
        return self.create_from_model(membership)

    def create_from_model(self, membership: Membership) -> str:
        ref = self.collection.document()
        membership.slug = build_slug(membership.name, membership.surname, suffix=ref.id[-6:])
        ref.set(membership.to_firestore(include_none=True))
        return ref.id

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

    def find_by_year(self, year: int) -> List[Membership]:
        docs = self.collection.where(
            filter=FieldFilter("membership_years", "array_contains", int(year))
        ).stream()
        return [self._model_from_snapshot(doc) for doc in docs]

    def update_from_model(self, membership_id: str, payload: Membership) -> bool:
        # Il repository non contiene regole di rinnovo: persiste il model già deciso dal service.
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

    def get_for_account(self, email: str, uid: str, *, allow_link: bool = False,
                        newsletter_consent: Optional[bool] = None) -> Membership:
        """Authorize a unique email/UID binding; commit only the requested fields."""
        denied = "Account not authorized for this membership"
        if not isinstance(email, str) or not email or not isinstance(uid, str) or not uid:
            raise ValidationError(denied)
        if newsletter_consent is not None and type(newsletter_consent) is not bool:
            raise ValidationError("Invalid newsletter consent")
        membership_id = None
        for _ in range(4):
            matches = self.collection.where(filter=FieldFilter("email", "==", email)).limit(2).get()
            if membership_id and (len(matches) != 1 or matches[0].id != membership_id):
                raise ValidationError(denied)
            if not matches and allow_link:
                raise NotFoundError("Membership not found for this account")
            if len(matches) != 1:
                raise ValidationError(denied)
            snapshot = matches[0]
            membership_id = snapshot.id
            data = snapshot.to_dict() or {}
            bound_uid = data.get("uid")
            changes = {}
            if bound_uid in (None, ""):
                if allow_link is not True:
                    raise ValidationError(denied)
                changes["uid"] = uid
            elif bound_uid != uid:
                raise ValidationError(denied)
            if newsletter_consent is not None:
                changes["newsletter_consent"] = newsletter_consent
            if not changes:
                return self._model_from_snapshot(snapshot)
            try:
                snapshot.reference.update(changes,
                    option=firestore.Client.write_option(last_update_time=snapshot.update_time))
            except (Aborted, FailedPrecondition):
                continue
            data.update(changes)
            return Membership.from_firestore(data, snapshot.id)
        raise ConflictError("Membership changed concurrently; retry the request")

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
