from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class MemberApiBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class MemberEventQueryDTO(MemberApiBaseDTO):
    event_id: str = Field(min_length=1, validation_alias=AliasChoices("event_id", "eventId"))


class MemberPreferencesPatchDTO(MemberApiBaseDTO):
    newsletter_consent: bool


class MemberRenewalItemDTO(MemberApiBaseDTO):
    year: Optional[int] = None
    date: Optional[str] = None
    fee: Optional[float] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MemberMeResponseDTO(MemberApiBaseDTO):
    id: str
    name: str = ""
    surname: str = ""
    email: str = ""
    subscription_valid: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    membership_years: List[int] = Field(default_factory=list)
    renewals: List[Dict[str, Any]] = Field(default_factory=list)
    wallet_url: Optional[str] = None
    card_url: Optional[str] = None
    attended_events: List[str] = Field(default_factory=list)
    newsletter_consent: bool = True

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MemberEventItemDTO(MemberApiBaseDTO):
    id: str
    slug: str = ""
    title: str = ""
    date: Optional[str] = None
    location_hint: str = ""
    image: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MemberPurchaseItemDTO(MemberApiBaseDTO):
    id: str
    type: str = ""
    ref_id: str = ""
    amount_total: str = ""
    currency: str = ""
    timestamp: Optional[str] = None
    payment_method: str = ""
    event_title: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MemberTicketResponseDTO(MemberApiBaseDTO):
    is_participant: bool = False
    ticket_pdf_url: Optional[str] = None
    wallet_url: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
