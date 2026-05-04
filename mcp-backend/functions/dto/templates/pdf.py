from typing import Optional

from pydantic import BaseModel, ConfigDict


class TicketPdfPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logo_url: str
    title: str
    full_name: str
    membership_id: Optional[str] = None
    date: str
    time: str
    location: str


class MembershipCardPdfPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logo_url: str
    full_name: str
    membership_id: str
    expiry_date: str
    expiry_year: str = ""
