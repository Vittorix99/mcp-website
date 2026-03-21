from dataclasses import dataclass
from typing import Optional

from .membership import Membership


@dataclass(frozen=True)
class MembershipPass:
    membership_id: str
    name: str
    validity: str
    mail: str

    @classmethod
    def from_membership(
        cls,
        membership_id: str,
        membership: Membership,
        validity: str,
    ) -> "MembershipPass":
        full_name = f"{membership.name or ''} {membership.surname or ''}".strip()
        return cls(
            membership_id=membership_id,
            name=full_name,
            validity=validity,
            mail=membership.email or "",
        )

    def to_pass2u_payload(self, expiration_date: Optional[str] = None) -> dict:
        payload = {
            "barcode": {
                "message": self.membership_id,
                "altText": self.membership_id,
            },
            "fields": [
                {"key": "name", "value": self.name},
                {"key": "validity", "value": self.validity},
                {"key": "mail", "value": self.mail},
            ],
        }
        if expiration_date:
            payload["expirationDate"] = expiration_date
        return payload


@dataclass(frozen=True)
class MembershipPassResult:
    pass_id: str
    wallet_url: str
    apple_wallet_url: str
    google_wallet_url: str

    @classmethod
    def from_pass_id(cls, pass_id: str) -> "MembershipPassResult":
        wallet_url = f"https://www.pass2u.net/d/{pass_id}"
        return cls(
            pass_id=pass_id,
            wallet_url=wallet_url,
            apple_wallet_url=wallet_url,
            google_wallet_url=wallet_url,
        )
