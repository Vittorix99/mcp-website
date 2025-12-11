from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models import Membership


@dataclass
class MembershipDTO:
    """DTO representing a membership profile."""

    id: Optional[str] = None
    name: str = ""
    surname: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    subscription_valid: bool = True
    membership_sent: bool = False
    membership_type: str = "manual"
    purchase_id: Optional[str] = None
    purchases: List[str] = field(default_factory=list)
    attended_events: List[str] = field(default_factory=list)
    card_url: Optional[str] = None
    card_storage_path: Optional[str] = None
    send_card_on_create: bool = False
    membership_fee: Optional[float] = None

    @classmethod
    def from_model(cls, membership: Membership) -> "MembershipDTO":
        return cls(
            id=membership.id,
            name=membership.name,
            surname=membership.surname,
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
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
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
        }
        return {k: v for k, v in payload.items() if v is not None}
