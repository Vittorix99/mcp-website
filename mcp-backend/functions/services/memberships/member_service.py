import logging
from typing import List, Optional

from config.external_services import SENDER_GROUP_MEMBERS
from dto.member_api import (
    MemberEventItemDTO,
    MemberMeResponseDTO,
    MemberPurchaseItemDTO,
    MemberTicketResponseDTO,
)
from errors.service_errors import NotFoundError, ValidationError
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.sender.sender_service import SenderService
from utils.safe_logging import mask_email, redact_sensitive


def _fmt_date(val) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


class MemberService:
    def __init__(
        self,
        membership_repository: Optional[MembershipRepository] = None,
        event_repository: Optional[EventRepository] = None,
        purchase_repository: Optional[PurchaseRepository] = None,
        participant_repository: Optional[ParticipantRepository] = None,
        sender_service: Optional[SenderService] = None,
    ):
        self.logger = logging.getLogger("MemberService")
        self.membership_repository = membership_repository or MembershipRepository()
        self.event_repository = event_repository or EventRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.sender_service = sender_service or SenderService()

    def _get_membership_by_email(self, email: str, uid: str = ""):
        """Fetch membership by email; self-heal uid if missing."""
        if not email:
            raise ValidationError("Token has no email claim")
        membership = self.membership_repository.find_by_email(email)
        if not membership:
            raise NotFoundError("Membership not found for this account")
        if uid and not membership.uid:
            try:
                self.membership_repository.set_uid(membership.id, uid)
                membership.uid = uid
            except Exception as exc:
                self.logger.warning(
                    "_get_membership_by_email: uid self-heal failed: %s",
                    redact_sensitive(str(exc)),
                )
        return membership

    def get_me(self, email: str, uid: str = "") -> MemberMeResponseDTO:
        membership = self._get_membership_by_email(email, uid)
        renewals_raw = membership.renewals or []
        renewals_out = [
            {
                "year": r.get("year") if isinstance(r, dict) else None,
                "date": _fmt_date(r.get("date")) if isinstance(r, dict) else None,
                "fee": r.get("fee") if isinstance(r, dict) else None,
            }
            for r in renewals_raw
            if isinstance(r, dict)
        ]
        return MemberMeResponseDTO(
            id=membership.id,
            name=membership.name or "",
            surname=membership.surname or "",
            email=membership.email or "",
            subscription_valid=bool(membership.subscription_valid),
            start_date=_fmt_date(membership.start_date),
            end_date=_fmt_date(membership.end_date),
            membership_years=membership.membership_years or [],
            renewals=renewals_out,
            wallet_url=membership.wallet_url or None,
            card_url=membership.card_url or None,
            attended_events=membership.attended_events or [],
            newsletter_consent=bool(membership.newsletter_consent),
        )

    def get_attended_events(self, email: str, uid: str = "") -> List[MemberEventItemDTO]:
        membership = self._get_membership_by_email(email, uid)
        event_ids = membership.attended_events or []
        if not event_ids:
            return []

        events: List[MemberEventItemDTO] = []
        for event_id in event_ids:
            try:
                event = self.event_repository.get_model(event_id)
                if not event:
                    continue
                events.append(MemberEventItemDTO(
                    id=event.id,
                    slug=event.slug or "",
                    title=event.title or "",
                    date=_fmt_date(event.date),
                    location_hint=event.location_hint or "",
                    image=event.image or "",
                ))
            except Exception as exc:
                self.logger.warning(
                    "get_attended_events: failed to fetch event %s: %s",
                    event_id,
                    redact_sensitive(str(exc)),
                )

        events.sort(key=lambda e: e.date or "", reverse=True)
        return events

    def get_purchases(self, email: str, uid: str = "") -> List[MemberPurchaseItemDTO]:
        membership = self._get_membership_by_email(email, uid)
        purchase_ids = membership.purchases or []
        if not purchase_ids:
            return []

        results: List[MemberPurchaseItemDTO] = []
        for purchase_id in purchase_ids:
            try:
                purchase = self.purchase_repository.get_model(purchase_id)
                if not purchase:
                    continue

                event_title = None
                if purchase.purchase_type and str(purchase.purchase_type.value) == "event" and purchase.ref_id:
                    try:
                        event = self.event_repository.get_model(purchase.ref_id)
                        if event:
                            event_title = event.title or None
                    except Exception:
                        pass

                results.append(MemberPurchaseItemDTO(
                    id=purchase.id,
                    type=purchase.purchase_type.value if purchase.purchase_type else "",
                    ref_id=purchase.ref_id or "",
                    amount_total=str(purchase.amount_total or ""),
                    currency=purchase.currency or "",
                    timestamp=_fmt_date(purchase.timestamp),
                    payment_method=purchase.payment_method or "",
                    event_title=event_title,
                ))
            except Exception as exc:
                self.logger.warning(
                    "get_purchases: failed to fetch purchase %s: %s",
                    purchase_id,
                    redact_sensitive(str(exc)),
                )

        results.sort(key=lambda p: p.timestamp or "", reverse=True)
        return results

    def get_ticket(self, email: str, uid: str, event_id: str) -> MemberTicketResponseDTO:
        membership = self._get_membership_by_email(email, uid)
        participant = self.participant_repository.get_by_membership_id(event_id, membership.id)
        if not participant:
            return MemberTicketResponseDTO(is_participant=False)
        return MemberTicketResponseDTO(
            is_participant=True,
            ticket_pdf_url=participant.ticket_pdf_url or None,
            wallet_url=membership.wallet_url or None,
        )

    def patch_preferences(
        self,
        email: str,
        uid: str,
        newsletter_consent: bool,
    ) -> dict:
        membership = self._get_membership_by_email(email, uid)
        membership.newsletter_consent = newsletter_consent
        self.membership_repository.update_from_model(membership.id, membership)

        if email and SENDER_GROUP_MEMBERS:
            try:
                if newsletter_consent:
                    self.sender_service.upsert_subscriber(
                        email=email,
                        firstname=membership.name or None,
                        lastname=membership.surname or None,
                        groups=[SENDER_GROUP_MEMBERS],
                    )
                    self.logger.info(
                        "patch_preferences: re-subscribed %s to members group", mask_email(email)
                    )
                else:
                    self.sender_service.remove_from_group(email, SENDER_GROUP_MEMBERS)
                    self.logger.info(
                        "patch_preferences: removed %s from members group", mask_email(email)
                    )
            except Exception as exc:
                self.logger.error(
                    "patch_preferences: Sender sync failed for %s: %s",
                    mask_email(email),
                    redact_sensitive(str(exc)),
                )

        return {"success": True}
