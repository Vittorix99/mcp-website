from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import FirestoreModel


@dataclass
class Membership(FirestoreModel):
    """Represents a member profile stored in ``memberships``."""

    name: str = ""
    surname: str = ""
    slug: Optional[str] = field(default=None, metadata={"firestore_name": "slug"})
    email: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
    start_date: Optional[str] = field(default=None, metadata={"firestore_name": "start_date"})
    end_date: Optional[str] = field(default=None, metadata={"firestore_name": "end_date"})
    subscription_valid: bool = True
    membership_sent: bool = False
    membership_type: str = "manual"
    purchase_id: Optional[str] = field(default=None, metadata={"firestore_name": "purchase_id"})
    purchases: List[str] = field(default_factory=list)
    attended_events: List[str] = field(default_factory=list, metadata={"firestore_name": "attended_events"})
    renewals: List[Dict[str, Any]] = field(default_factory=list)
    membership_years: List[int] = field(default_factory=list, metadata={"firestore_name": "membership_years"})
    card_url: Optional[str] = None
    card_storage_path: Optional[str] = None
    send_card_on_create: bool = field(default=False, metadata={"firestore_name": "send_card_on_create"})
    membership_fee: Optional[float] = field(default=None, metadata={"firestore_name": "membership_fee"})
    wallet_pass_id: Optional[str] = field(default=None, metadata={"firestore_name": "wallet_pass_id"})
    wallet_url: Optional[str] = field(default=None, metadata={"firestore_name": "wallet_url"})
    uid: Optional[str] = field(default=None, metadata={"firestore_name": "uid"})
    newsletter_consent: bool = field(default=True, metadata={"firestore_name": "newsletter_consent"})


@dataclass(frozen=True)
class MembershipRef:
    email: str
    membership_id: str
