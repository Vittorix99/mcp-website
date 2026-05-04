from typing import Optional

from .common import EmailTemplateBasePayload


class MembershipEmailPayload(EmailTemplateBasePayload):
    full_name: str
    membership_id: str
    expiry_date: str
    membership_year: str
    wallet_url: Optional[str] = None
    pdf_url: Optional[str] = None
    apple_wallet_img: Optional[str] = None
    google_wallet_img: Optional[str] = None
