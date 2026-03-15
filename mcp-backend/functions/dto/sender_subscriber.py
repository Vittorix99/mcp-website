"""
DTO that represents a subscriber to be synced to Sender (sender.net).

Constructed from domain models (Membership, EventParticipant) so that
the sync layer is fully decoupled from raw Firestore dict access.

Sources are explicit and mutually exclusive today, but designed to diverge:
  - MEMBER        → person who has a paid/manual membership
  - TICKET_BUYER  → person who ticked newsletter_consent during ticket purchase
  - NEWSLETTER    → person who signed up via the public newsletter form
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from models.membership import Membership
from models.event_participant import EventParticipant


class SubscriberSource(str, Enum):
    MEMBER = "member"
    TICKET_BUYER = "ticket_buyer"
    NEWSLETTER = "newsletter"


@dataclass(frozen=True)
class SenderSubscriberDTO:
    email: str
    source: SubscriberSource
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    # Sender custom fields
    membership_id: Optional[str] = None
    event_id: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Factory methods
    # ------------------------------------------------------------------ #

    @classmethod
    def from_membership(cls, membership_id: str, membership: Membership) -> "SenderSubscriberDTO":
        """Build from a Membership model — subscriber source is MEMBER."""
        return cls(
            email=(membership.email or "").strip().lower(),
            source=SubscriberSource.MEMBER,
            firstname=membership.name or None,
            lastname=membership.surname or None,
            phone=membership.phone or None,
            membership_id=membership_id,
        )

    @classmethod
    def from_participant(
        cls,
        participant_id: str,
        participant: EventParticipant,
        event_id: str,
    ) -> "SenderSubscriberDTO":
        """
        Build from an EventParticipant model — subscriber source is TICKET_BUYER.
        Only call this when participant.newsletter_consent is True.
        """
        return cls(
            email=(participant.email or "").strip().lower(),
            source=SubscriberSource.TICKET_BUYER,
            firstname=participant.name or None,
            lastname=participant.surname or None,
            phone=participant.phone or None,
            membership_id=participant.membership_id or None,
            event_id=event_id,
        )

    @classmethod
    def from_newsletter_signup(
        cls,
        email: str,
        name: Optional[str] = None,
    ) -> "SenderSubscriberDTO":
        """Build from a direct newsletter signup — source is NEWSLETTER."""
        firstname = None
        if name:
            parts = name.strip().split(" ", 1)
            firstname = parts[0] or None
        return cls(
            email=email.strip().lower(),
            source=SubscriberSource.NEWSLETTER,
            firstname=firstname,
        )

    # ------------------------------------------------------------------ #
    # Serialisation helpers
    # ------------------------------------------------------------------ #

    def to_sender_fields(self) -> Optional[Dict[str, Any]]:
        """
        Returns the ``fields`` dict for Sender custom subscriber fields.
        Returns None if there are no custom fields to set.
        """
        custom: Dict[str, Any] = {}
        if self.membership_id:
            custom["membership_id"] = self.membership_id
        if self.event_id:
            custom["event_id"] = self.event_id
        if self.source:
            custom["source"] = self.source.value
        return custom or None

    def to_upsert_kwargs(self, groups: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Returns kwargs ready for SenderService.upsert_subscriber().
        ``groups`` is passed in by the caller since it depends on config,
        not on the DTO itself.
        """
        return {
            "email": self.email,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "phone": self.phone,
            "groups": groups,
            "fields": self.to_sender_fields(),
        }
