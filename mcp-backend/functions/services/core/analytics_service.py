from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from domain.event_rules import parse_event_date
from dto.analytics_api import (
    AgeBandDTO,
    AgeDistributionResponseDTO,
    AudienceBreakdownItemDTO,
    AudienceRetentionResponseDTO,
    DailySalesDTO,
    DashboardKpisResponseDTO,
    EntranceFlowBucketDTO,
    EntranceFlowResponseDTO,
    EventFunnelResponseDTO,
    GenderDistributionResponseDTO,
    MembershipTrendResponseDTO,
    MonthlyMembershipDTO,
    RevenueBreakdownResponseDTO,
    RevenueTierDTO,
    SalesOverTimeResponseDTO,
)
from errors.service_errors import NotFoundError
from interfaces.repositories import (
    EntranceScanRepositoryProtocol,
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from models import PurchaseStatus, PurchaseTypes
from repositories.entrance_scan_repository import EntranceScanRepository
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository

logger = logging.getLogger("AnalyticsService")

ROMA_TZ = ZoneInfo("Europe/Rome")
PRICE_TOLERANCE = 0.50
TIER_NAMES = ("super_early", "early", "regular", "late")
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class AnalyticsService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        entrance_scan_repository: Optional[EntranceScanRepositoryProtocol] = None,
    ):
        self.event_repository = event_repository or EventRepository()
        self.membership_repository = membership_repository or MembershipRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.entrance_scan_repository = entrance_scan_repository or EntranceScanRepository()

    # ---- Public API -------------------------------------------------------

    def get_entrance_flow(
        self,
        event_id: str,
        start_time: Optional[str] = None,
        span_hours: int = 6,
        bucket_minutes: int = 30,
    ) -> EntranceFlowResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        scans = self.entrance_scan_repository.list(event_id)
        safe_span_hours = max(1, min(24, self._safe_int(span_hours) or 6))
        safe_bucket_minutes = self._sanitize_bucket_minutes(bucket_minutes)

        start_clock = (
            self._parse_clock(start_time)
            or self._parse_clock(getattr(event, "start_time", None))
            or time(22, 0)
        )
        start_minutes = start_clock.hour * 60 + start_clock.minute
        window_start_minutes = start_minutes
        window_end_minutes = start_minutes + safe_span_hours * 60
        buckets_count = max(1, int((safe_span_hours * 60) // safe_bucket_minutes))

        counts = [0] * buckets_count
        for scan in scans:
            ts = self._to_datetime(getattr(scan, "scanned_at", None))
            if not ts:
                continue
            local = ts.astimezone(ROMA_TZ)
            minute_of_day = local.hour * 60 + local.minute
            # Orari post-mezzanotte appartengono alla stessa finestra notturna
            # quando sono "prima" dell'ora di inizio (es. start 22:00, scan 01:20).
            if minute_of_day < start_minutes:
                minute_of_day += 24 * 60
            if minute_of_day < window_start_minutes or minute_of_day >= window_end_minutes:
                continue
            idx = (minute_of_day - window_start_minutes) // safe_bucket_minutes
            if 0 <= idx < buckets_count:
                counts[idx] += 1

        buckets = []
        cumulative = 0
        for i in range(buckets_count):
            slot_start_min = (window_start_minutes + i * safe_bucket_minutes) % (24 * 60)
            label = f"{slot_start_min // 60:02d}:{slot_start_min % 60:02d}"
            count = counts[i]
            cumulative += count
            buckets.append(EntranceFlowBucketDTO(
                hour_label=label,
                count=count,
                cumulative=cumulative,
            ))

        return EntranceFlowResponseDTO(
            event_id=event_id,
            event_title=event.title or "",
            total_scanned=sum(counts),
            buckets=buckets,
        )

    def get_sales_over_time(self, event_id: str) -> SalesOverTimeResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        event_date = self._parse_date_like(getattr(event, "date", None))
        created_at = self._to_datetime(getattr(event, "created_at", None))

        if not created_at:
            epoch = datetime.combine(
                event_date or date.today(), time(0, 0), tzinfo=timezone.utc
            )
        else:
            epoch = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)

        publication_date_str = epoch.astimezone(ROMA_TZ).strftime("%Y-%m-%d")
        event_date_str = event.date or ""

        purchases = [
            p for p in self.purchase_repository.list_models_by_ref_id(event_id)
            if self._is_valid_event_purchase(p)
        ]

        max_participants = self._safe_int(getattr(event, "max_participants", 0))
        by_day: Dict[int, int] = defaultdict(int)

        for purchase in purchases:
            ts = self._to_datetime(getattr(purchase, "timestamp", None))
            if not ts:
                continue
            day_number = max(0, int((ts.timestamp() - epoch.timestamp()) / 86400))
            by_day[day_number] += self._safe_int(getattr(purchase, "participants_count", 0))

        daily_sales = []
        cumulative = 0
        for day_num in sorted(by_day.keys()):
            day_date = (epoch + timedelta(days=day_num)).astimezone(ROMA_TZ).strftime("%Y-%m-%d")
            sold = by_day[day_num]
            cumulative += sold
            daily_sales.append(DailySalesDTO(
                day=day_num,
                date=day_date,
                tickets_sold=sold,
                cumulative=cumulative,
            ))

        total_sold = cumulative

        return SalesOverTimeResponseDTO(
            event_id=event_id,
            event_title=event.title or "",
            publication_date=publication_date_str,
            event_date=event_date_str,
            total_sold=total_sold,
            max_participants=max_participants,
            daily_sales=daily_sales,
        )

    def get_audience_retention(self, event_id: str) -> AudienceRetentionResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        current_event_date = self._parse_date_like(getattr(event, "date", None))

        # Find all events with dates strictly before the current event
        previous_event_ids = set()
        for ev in self.event_repository.stream_models():
            if ev.id == event_id:
                continue
            ev_date = self._parse_date_like(getattr(ev, "date", None))
            if ev_date and current_event_date and ev_date < current_event_date:
                previous_event_ids.add(ev.id)

        # Count how many previous events each membership attended
        membership_prev_count: Dict[str, int] = defaultdict(int)
        for prev_id in previous_event_ids:
            for p in self.participant_repository.list(prev_id):
                mid = (getattr(p, "membership_id", None) or "").strip()
                if mid:
                    membership_prev_count[mid] += 1

        # Classify current participants
        current_participants = self.participant_repository.list(event_id)
        first_time = 0
        second_third = 0
        four_plus = 0

        for p in current_participants:
            mid = (getattr(p, "membership_id", None) or "").strip()
            if not mid:
                first_time += 1
                continue
            prev_count = membership_prev_count.get(mid, 0)
            if prev_count == 0:
                first_time += 1
            elif prev_count <= 2:
                second_third += 1
            else:
                four_plus += 1

        total = len(current_participants)

        def pct(n: int) -> float:
            return round(n / total * 100, 1) if total > 0 else 0.0

        return AudienceRetentionResponseDTO(
            event_id=event_id,
            event_title=event.title or "",
            total_participants=total,
            new=first_time,
            returning=second_third + four_plus,
            breakdown=[
                AudienceBreakdownItemDTO(category="First time", count=first_time, pct=pct(first_time)),
                AudienceBreakdownItemDTO(category="2nd–3rd event", count=second_third, pct=pct(second_third)),
                AudienceBreakdownItemDTO(category="4+ events", count=four_plus, pct=pct(four_plus)),
            ],
        )

    def get_revenue_breakdown(self, event_id: str) -> RevenueBreakdownResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        purchases = [
            p for p in self.purchase_repository.list_models_by_ref_id(event_id)
            if self._is_valid_event_purchase(p)
        ]

        rows = []
        for purchase in purchases:
            count = self._safe_int(getattr(purchase, "participants_count", 0))
            if count <= 0:
                continue
            gross = self._safe_amount(getattr(purchase, "amount_total", 0))
            net = self._safe_amount(getattr(purchase, "net_amount", 0))
            rows.append({
                "purchase_id": getattr(purchase, "id", None),
                "count": count,
                "gross": gross,
                "net": net,
                "unit_price": gross / count,
            })

        tier_map = self._map_tiers(rows)

        aggregates: Dict[str, Dict] = {
            name: {"tier": name, "count": 0, "gross": 0.0, "net": 0.0}
            for name in TIER_NAMES
        }
        for row in rows:
            tier_name = tier_map.get(row["purchase_id"], "regular")
            b = aggregates[tier_name]
            b["count"] += row["count"]
            b["gross"] += row["gross"]
            b["net"] += row["net"]

        by_tier = []
        total_gross = 0.0
        total_net = 0.0
        for name in TIER_NAMES:
            b = aggregates[name]
            if b["count"] == 0:
                continue
            avg = round(b["gross"] / b["count"], 2) if b["count"] > 0 else 0.0
            by_tier.append(RevenueTierDTO(
                tier=name,
                count=b["count"],
                gross=round(b["gross"], 2),
                net=round(b["net"], 2),
                avg_unit_price=avg,
            ))
            total_gross += b["gross"]
            total_net += b["net"]

        return RevenueBreakdownResponseDTO(
            event_id=event_id,
            event_title=event.title or "",
            total_gross=round(total_gross, 2),
            total_net=round(total_net, 2),
            paypal_fees=round(total_gross - total_net, 2),
            by_tier=by_tier,
        )

    def get_event_funnel(self, event_id: str) -> EventFunnelResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        purchases = [
            p for p in self.purchase_repository.list_models_by_ref_id(event_id)
            if self._is_valid_event_purchase(p)
        ]
        tickets_sold = sum(
            self._safe_int(getattr(p, "participants_count", 0)) for p in purchases
        )

        participants = self.participant_repository.list(event_id)
        entered_flag = sum(1 for p in participants if bool(getattr(p, "entered", False)))

        scanned = len(self.entrance_scan_repository.list(event_id))
        max_participants = self._safe_int(getattr(event, "max_participants", 0))

        return EventFunnelResponseDTO(
            event_id=event_id,
            event_title=event.title or "",
            tickets_sold=tickets_sold,
            entered_flag=entered_flag,
            scanned=scanned,
            max_participants=max_participants,
            fill_rate_pct=self._pct(tickets_sold, max_participants),
            show_rate_pct=self._pct(entered_flag, tickets_sold),
            scan_coverage_pct=self._pct(scanned, entered_flag),
        )

    def get_gender_distribution(self, event_id: str) -> GenderDistributionResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        participants = self.participant_repository.list(event_id)
        male = sum(
            1 for p in participants
            if self._normalize_gender(getattr(p, "gender", None)) == "male"
        )
        female = sum(
            1 for p in participants
            if self._normalize_gender(getattr(p, "gender", None)) == "female"
        )
        unknown = sum(
            1 for p in participants
            if self._normalize_gender(getattr(p, "gender", None)) == "unknown"
        )
        total = len(participants)

        def pct(n: int) -> float:
            return round(n / total * 100, 1) if total > 0 else 0.0

        return GenderDistributionResponseDTO(
            event_id=event_id,
            male=male,
            female=female,
            unknown=unknown,
            male_pct=pct(male),
            female_pct=pct(female),
            unknown_pct=pct(unknown),
        )

    _AGE_BANDS = (
        ("18-20", 18, 20),
        ("21-24", 21, 24),
        ("25-29", 25, 29),
        ("30-34", 30, 34),
        ("35+",   35, 200),
    )

    def get_age_distribution(self, event_id: str) -> AgeDistributionResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError(f"Evento non trovato: {event_id}")

        participants = self.participant_repository.list(event_id)
        counts: Dict[str, int] = {band: 0 for band, _, _ in self._AGE_BANDS}
        counts["unknown"] = 0

        for p in participants:
            age = self._age_from_birthdate(getattr(p, "birthdate", None))
            if age is None:
                counts["unknown"] += 1
                continue
            matched = False
            for band, start, end in self._AGE_BANDS:
                if start <= age <= end:
                    counts[band] += 1
                    matched = True
                    break
            if not matched:
                counts["unknown"] += 1

        total = len(participants)
        dominant = max(counts, key=lambda k: counts[k]) if total > 0 else "unknown"

        def pct(n: int) -> float:
            return round(n / total * 100, 1) if total > 0 else 0.0

        bands = [
            AgeBandDTO(band=band, count=counts[band], pct=pct(counts[band]))
            for band, _, _ in self._AGE_BANDS
        ]
        bands.append(AgeBandDTO(band="unknown", count=counts["unknown"], pct=pct(counts["unknown"])))

        return AgeDistributionResponseDTO(event_id=event_id, total=total, dominant=dominant, bands=bands)

    def _age_from_birthdate(self, value: Any) -> Optional[int]:
        from datetime import date as date_type
        if value is None:
            return None
        if isinstance(value, datetime):
            birth = value.date()
        elif isinstance(value, date_type):
            birth = value
        elif isinstance(value, str):
            birth = self._parse_date_like(value)
            if not birth:
                return None
        else:
            return None
        if not birth:
            return None
        today = datetime.now(ROMA_TZ).date()
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return age if 0 <= age <= 120 else None

    def get_membership_trend(self, year: int) -> MembershipTrendResponseDTO:
        all_memberships = list(self.membership_repository.stream())
        total_active = sum(
            1 for m in all_memberships if bool(getattr(m, "subscription_valid", False))
        )

        by_month: Dict[str, int] = defaultdict(int)
        for m in all_memberships:
            years = getattr(m, "membership_years", []) or []
            if not isinstance(years, list):
                years = []
            if year not in years:
                continue
            created = self._to_datetime(getattr(m, "start_date", None))
            if not created:
                continue
            local = created.astimezone(ROMA_TZ)
            if local.year != year:
                continue
            month_key = f"{year}-{local.month:02d}"
            by_month[month_key] += 1

        monthly = []
        for i in range(1, 13):
            key = f"{year}-{i:02d}"
            monthly.append(MonthlyMembershipDTO(
                month=key,
                label=MONTH_LABELS[i - 1],
                new_members=by_month.get(key, 0),
            ))

        total_year = sum(item.new_members for item in monthly)

        return MembershipTrendResponseDTO(
            year=year,
            total_year=total_year,
            total_active=total_active,
            monthly=monthly,
        )

    def get_dashboard_kpis(self) -> DashboardKpisResponseDTO:
        events = list(self.event_repository.stream_models())
        purchases = [
            p for p in self.purchase_repository.stream_models()
            if self._is_valid_event_purchase(p)
        ]
        members_count = sum(
            1 for m in self.membership_repository.stream()
            if bool(getattr(m, "subscription_valid", False))
        )

        revenue_net_total = sum(
            self._safe_amount(getattr(p, "net_amount", 0)) for p in purchases
        )

        now_local = datetime.now(ROMA_TZ)
        revenue_net_month = sum(
            self._safe_amount(getattr(p, "net_amount", 0))
            for p in purchases
            if self._in_current_month(getattr(p, "timestamp", None), now_local)
        )

        # participants count (unique membership_ids across all events)
        unique_keys: set = set()
        for ev in events:
            if not ev.id:
                continue
            for p in self.participant_repository.list(ev.id):
                mid = (getattr(p, "membership_id", None) or "").strip().lower()
                email = (getattr(p, "email", None) or "").strip().lower()
                key = mid or email or f"{getattr(p, 'name', '')}:{getattr(p, 'surname', '')}:{ev.id}"
                if key:
                    unique_keys.add(key)

        # avg fill rate
        fill_rates = []
        for ev in events:
            max_p = self._safe_int(getattr(ev, "max_participants", 0))
            if max_p <= 0:
                continue
            count = sum(1 for _ in self.participant_repository.list(ev.id)) if ev.id else 0
            fill_rates.append(count / max_p * 100)
        avg_fill_rate = round(sum(fill_rates) / len(fill_rates), 2) if fill_rates else 0.0

        # omaggi
        total_omaggi = 0
        for ev in events:
            if not ev.id:
                continue
            for p in self.participant_repository.list(ev.id):
                pm = self._normalize_payment_method(getattr(p, "payment_method", None))
                if pm == "omaggio":
                    total_omaggi += 1

        # avg unit payment
        gross_total = sum(self._safe_amount(getattr(p, "amount_total", 0)) for p in purchases)
        ticket_total = sum(self._safe_int(getattr(p, "participants_count", 0)) for p in purchases)
        avg_unit_payment = round(gross_total / ticket_total, 2) if ticket_total > 0 else 0.0

        return DashboardKpisResponseDTO(
            total_revenue_net=round(revenue_net_total, 2),
            events_count=len(events),
            members_count=members_count,
            participants_count=len(unique_keys),
            avg_fill_rate=avg_fill_rate,
            this_month_revenue=round(revenue_net_month, 2),
            total_omaggi=total_omaggi,
            avg_unit_payment=avg_unit_payment,
        )

    # ---- Internal helpers ------------------------------------------------

    _VALID_EVENT_TYPE_VALUES = {PurchaseTypes.EVENT.value, "event_and_membership"}

    def _is_valid_event_purchase(self, purchase: Any) -> bool:
        purchase_type = getattr(purchase, "purchase_type", None)
        type_value = str(getattr(purchase_type, "value", purchase_type or "")).lower()
        if type_value not in self._VALID_EVENT_TYPE_VALUES:
            return False
        if not getattr(purchase, "ref_id", None):
            return False
        if self._safe_int(getattr(purchase, "participants_count", 0)) <= 0:
            return False
        status = str(getattr(purchase, "status", "") or "").upper()
        capture = str(getattr(purchase, "capture_status", "") or "").upper()
        bad = PurchaseStatus.invalid_statuses()
        return status not in bad and capture not in bad

    def _map_tiers(self, rows: List[Dict]) -> Dict[Optional[str], str]:
        if not rows:
            return {}
        clustered = []
        for row in sorted(rows, key=lambda r: r["unit_price"]):
            placed = False
            for cluster in clustered:
                if abs(row["unit_price"] - cluster["center"]) <= PRICE_TOLERANCE:
                    cluster["rows"].append(row)
                    cluster["center"] = sum(r["unit_price"] for r in cluster["rows"]) / len(cluster["rows"])
                    placed = True
                    break
            if not placed:
                clustered.append({"center": row["unit_price"], "rows": [row]})

        clustered.sort(key=lambda c: c["center"])
        n = len(clustered)
        cluster_to_tier = {}
        if n <= 1:
            cluster_to_tier = {0: "regular"}
        elif n == 2:
            cluster_to_tier = {0: "early", 1: "regular"}
        elif n == 3:
            cluster_to_tier = {0: "early", 1: "regular", 2: "late"}
        else:
            for i in range(n):
                if i == 0:
                    cluster_to_tier[i] = "super_early"
                elif i == 1:
                    cluster_to_tier[i] = "early"
                elif i == n - 1:
                    cluster_to_tier[i] = "late"
                else:
                    cluster_to_tier[i] = "regular"

        mapping: Dict[Optional[str], str] = {}
        for i, cluster in enumerate(clustered):
            tier = cluster_to_tier.get(i, "regular")
            for row in cluster["rows"]:
                mapping[row.get("purchase_id")] = tier
        return mapping

    def _normalize_gender(self, value: Any) -> str:
        raw = str(value or "").strip().lower()
        if raw in {"male", "maschio", "m"}:
            return "male"
        if raw in {"female", "femmina", "f"}:
            return "female"
        return "unknown"

    def _normalize_payment_method(self, value: Any) -> str:
        raw = getattr(value, "value", value)
        return str(raw or "unknown").strip().lower()

    def _pct(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(numerator / denominator * 100, 1)

    def _in_current_month(self, timestamp: Any, now_local: datetime) -> bool:
        ts = self._to_datetime(timestamp)
        if not ts:
            return False
        local = ts.astimezone(ROMA_TZ)
        return local.year == now_local.year and local.month == now_local.month

    def _parse_date_like(self, value: Any) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        raw = str(value).strip()
        if not raw:
            return None
        parsed = parse_event_date(raw)
        if parsed:
            return parsed
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        dt = self._to_datetime(raw)
        return dt.date() if dt else None

    def _to_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if hasattr(value, "to_datetime") and callable(value.to_datetime):
            try:
                dt = value.to_datetime()
                return dt if (dt and dt.tzinfo) else (dt.replace(tzinfo=timezone.utc) if dt else None)
            except Exception:
                return None
        if isinstance(value, (int, float)):
            try:
                secs = value / 1000.0 if value > 1e12 else value
                return datetime.fromtimestamp(secs, tz=timezone.utc)
            except Exception:
                return None
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return None

    def _safe_amount(self, value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _sanitize_bucket_minutes(self, value: Any) -> int:
        allowed = {5, 10, 15, 30, 60}
        minutes = self._safe_int(value)
        return minutes if minutes in allowed else 30

    def _parse_clock(self, value: Any) -> Optional[time]:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        parts = raw.split(":")
        if len(parts) < 2:
            return None
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except (TypeError, ValueError):
            return None
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return time(hour, minute)
