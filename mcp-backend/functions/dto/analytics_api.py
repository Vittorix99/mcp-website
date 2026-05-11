from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyticsBaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ---- Request DTOs --------------------------------------------------------

class EventAnalyticsQueryDTO(AnalyticsBaseDTO):
    event_id: str = Field(min_length=1)
    start_time: Optional[str] = Field(default=None)
    span_hours: int = Field(default=6, ge=1, le=24)
    bucket_minutes: int = Field(default=30)

    @field_validator("start_time", mode="before")
    @classmethod
    def normalize_start_time(cls, v):
        if v is None:
            return None
        raw = str(v).strip()
        if not raw:
            return None
        parts = raw.split(":")
        if len(parts) < 2:
            raise ValueError("start_time deve essere nel formato HH:MM")
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except (TypeError, ValueError):
            raise ValueError("start_time deve essere nel formato HH:MM")
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("start_time fuori range")
        return f"{hour:02d}:{minute:02d}"

    @field_validator("bucket_minutes", mode="before")
    @classmethod
    def validate_bucket_minutes(cls, v):
        try:
            value = int(v)
        except (TypeError, ValueError):
            raise ValueError("bucket_minutes non valido")
        allowed = {5, 10, 15, 30, 60}
        if value not in allowed:
            raise ValueError(f"bucket_minutes deve essere uno tra {sorted(allowed)}")
        return value


class MembershipTrendQueryDTO(AnalyticsBaseDTO):
    year: int = Field(default=0, ge=0, le=2200)

    @field_validator("year", mode="before")
    @classmethod
    def default_current_year(cls, v):
        if not v:
            from datetime import datetime
            return datetime.now().year
        return int(v)


# ---- Shared Response base ------------------------------------------------

class _ResponseBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


# ---- Entrance Flow -------------------------------------------------------

class EntranceFlowBucketDTO(_ResponseBase):
    hour_label: str = Field(serialization_alias="hourLabel")
    count: int
    cumulative: int


class EntranceFlowResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    event_title: str = Field(serialization_alias="eventTitle")
    total_scanned: int = Field(serialization_alias="totalScanned")
    buckets: List[EntranceFlowBucketDTO]


# ---- Sales Over Time -----------------------------------------------------

class DailySalesDTO(_ResponseBase):
    day: int
    date: str
    tickets_sold: int = Field(serialization_alias="ticketsSold")
    cumulative: int


class SalesOverTimeResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    event_title: str = Field(serialization_alias="eventTitle")
    publication_date: str = Field(serialization_alias="publicationDate")
    event_date: str = Field(serialization_alias="eventDate")
    total_sold: int = Field(serialization_alias="totalSold")
    max_participants: int = Field(serialization_alias="maxParticipants")
    daily_sales: List[DailySalesDTO] = Field(serialization_alias="dailySales")


# ---- Audience Retention --------------------------------------------------

class AudienceBreakdownItemDTO(_ResponseBase):
    category: str
    count: int
    pct: float


class AudienceRetentionResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    event_title: str = Field(serialization_alias="eventTitle")
    total_participants: int = Field(serialization_alias="totalParticipants")
    new: int
    returning: int
    breakdown: List[AudienceBreakdownItemDTO]


# ---- Revenue Breakdown ---------------------------------------------------

class RevenueTierDTO(_ResponseBase):
    tier: str
    count: int
    gross: float
    net: float
    avg_unit_price: float = Field(serialization_alias="avgUnitPrice")


class RevenueBreakdownResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    event_title: str = Field(serialization_alias="eventTitle")
    total_gross: float = Field(serialization_alias="totalGross")
    total_net: float = Field(serialization_alias="totalNet")
    paypal_fees: float = Field(serialization_alias="paypalFees")
    by_tier: List[RevenueTierDTO] = Field(serialization_alias="byTier")


# ---- Event Funnel --------------------------------------------------------

class EventFunnelResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    event_title: str = Field(serialization_alias="eventTitle")
    tickets_sold: int = Field(serialization_alias="ticketsSold")
    entered_flag: int = Field(serialization_alias="enteredFlag")
    scanned: int
    max_participants: int = Field(serialization_alias="maxParticipants")
    fill_rate_pct: float = Field(serialization_alias="fillRatePct")
    show_rate_pct: float = Field(serialization_alias="showRatePct")
    scan_coverage_pct: float = Field(serialization_alias="scanCoveragePct")


# ---- Age Distribution ----------------------------------------------------

class AgeBandDTO(_ResponseBase):
    band: str
    count: int
    pct: float


class AgeDistributionResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    total: int
    dominant: str
    bands: List[AgeBandDTO]


# ---- Gender Distribution -------------------------------------------------

class GenderDistributionResponseDTO(_ResponseBase):
    event_id: str = Field(serialization_alias="eventId")
    male: int
    female: int
    unknown: int
    male_pct: float = Field(serialization_alias="malePct")
    female_pct: float = Field(serialization_alias="femalePct")
    unknown_pct: float = Field(serialization_alias="unknownPct")


# ---- Membership Trend ----------------------------------------------------

class MonthlyMembershipDTO(_ResponseBase):
    month: str
    label: str
    new_members: int = Field(serialization_alias="newMembers")


class MembershipTrendResponseDTO(_ResponseBase):
    year: int
    total_year: int = Field(serialization_alias="totalYear")
    total_active: int = Field(serialization_alias="totalActive")
    monthly: List[MonthlyMembershipDTO]


# ---- Dashboard KPIs ------------------------------------------------------

class DashboardKpisResponseDTO(_ResponseBase):
    total_revenue_net: float = Field(serialization_alias="totalRevenueNet")
    events_count: int = Field(serialization_alias="eventsCount")
    members_count: int = Field(serialization_alias="membersCount")
    participants_count: int = Field(serialization_alias="participantsCount")
    avg_fill_rate: float = Field(serialization_alias="avgFillRate")
    this_month_revenue: float = Field(serialization_alias="thisMonthRevenue")
    total_omaggi: int = Field(serialization_alias="totalOmaggi")
    avg_unit_payment: float = Field(serialization_alias="avgUnitPayment")
