from dataclasses import dataclass, fields
from typing import Any, Dict, List, Optional

from models import Membership


@dataclass
class MembershipDTO:
    """DTO representing a membership profile."""

    id: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    slug: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    subscription_valid: Optional[bool] = None
    membership_sent: Optional[bool] = None
    membership_type: Optional[str] = None
    purchase_id: Optional[str] = None
    purchases: Optional[List[str]] = None
    attended_events: Optional[List[str]] = None
    card_url: Optional[str] = None
    card_storage_path: Optional[str] = None
    send_card_on_create: Optional[bool] = None
    membership_fee: Optional[float] = None
    wallet_pass_id: Optional[str] = None
    wallet_url: Optional[str] = None

    @classmethod
    def from_model(cls, membership: Membership) -> "MembershipDTO":
        return cls(
            id=membership.id,
            name=membership.name,
            surname=membership.surname,
            slug=membership.slug,
            email=membership.email,
            phone=membership.phone,
            birthdate=membership.birthdate,
            start_date=membership.start_date,
            end_date=membership.end_date,
            subscription_valid=membership.subscription_valid,
            membership_sent=membership.membership_sent,
            membership_type=membership.membership_type,
            purchase_id=membership.purchase_id,
            purchases=membership.purchases or [],
            attended_events=membership.attended_events or [],
            card_url=membership.card_url,
            card_storage_path=membership.card_storage_path,
            send_card_on_create=membership.send_card_on_create,
            membership_fee=membership.membership_fee,
            wallet_pass_id=membership.wallet_pass_id,
            wallet_url=membership.wallet_url,
        )

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "MembershipDTO":
        def pick(key, alternate=None):
            if key in payload:
                return payload.get(key)
            if alternate and alternate in payload:
                return payload.get(alternate)
            return None

        def pick_bool(key, alternate=None):
            if key in payload:
                value = payload.get(key)
                return None if value is None else bool(value)
            if alternate and alternate in payload:
                value = payload.get(alternate)
                return None if value is None else bool(value)
            return None

        return cls(
            id=payload.get("id") or payload.get("membership_id"),
            name=pick("name"),
            surname=pick("surname"),
            slug=payload.get("slug"),
            email=pick("email"),
            phone=pick("phone"),
            birthdate=pick("birthdate"),
            start_date=pick("start_date", "startDate"),
            end_date=pick("end_date", "endDate"),
            subscription_valid=pick_bool("subscription_valid"),
            membership_sent=pick_bool("membership_sent"),
            membership_type=pick("membership_type", "membershipType"),
            purchase_id=pick("purchase_id"),
            purchases=pick("purchases"),
            attended_events=pick("attended_events"),
            card_url=pick("card_url"),
            card_storage_path=pick("card_storage_path"),
            send_card_on_create=pick_bool("send_card_on_create", "sendCardOnCreate"),
            membership_fee=pick("membership_fee", "membershipFee"),
            wallet_pass_id=pick("wallet_pass_id"),
            wallet_url=pick("wallet_url"),
        )

    def to_update_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for f in fields(self):
            if f.name == "id":
                continue
            value = getattr(self, f.name)
            if value is not None:
                payload[f.name] = value
        return payload

    def apply_updates(self, membership: Membership) -> Membership:
        for f in fields(self):
            if f.name == "id":
                continue
            value = getattr(self, f.name)
            if value is not None:
                setattr(membership, f.name, value)
        return membership

    def validate_protected_fields(self) -> Optional[str]:
        if self.slug is not None:
            return "Modifica a campi riservati non consentita"
        if self.card_url is not None:
            return "Modifica diretta di card_url non consentita"
        if self.card_storage_path is not None or self.purchase_id is not None:
            return "Modifica a campi riservati non consentita"
        return None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "slug": self.slug,
            "email": self.email,
            "phone": self.phone,
            "birthdate": self.birthdate,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "subscription_valid": self.subscription_valid,
            "membership_sent": self.membership_sent,
            "membership_type": self.membership_type,
            "purchase_id": self.purchase_id,
            "purchases": self.purchases,
            "attended_events": self.attended_events,
            "card_url": self.card_url,
            "card_storage_path": self.card_storage_path,
            "send_card_on_create": self.send_card_on_create,
            "membership_fee": self.membership_fee,
            "wallet_pass_id": self.wallet_pass_id,
            "wallet_url": self.wallet_url,
        }
        return {k: v for k, v in payload.items() if v is not None}
