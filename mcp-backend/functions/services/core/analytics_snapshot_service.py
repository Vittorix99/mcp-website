from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from domain.event_rules import parse_event_date
from interfaces.repositories import (
    EntranceScanRepositoryProtocol,
    EventRepositoryProtocol,
    JobRepositoryProtocol,
    MembershipRepositoryProtocol,
    MessageRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from models import AnalyticsJob, PurchaseStatus, PurchaseTypes
from repositories.analytics_snapshot_repository import AnalyticsSnapshotRepository
from repositories.entrance_scan_repository import EntranceScanRepository
from repositories.event_repository import EventRepository
from repositories.job_repository import AnalyticsJobRepository
from repositories.membership_repository import MembershipRepository
from repositories.message_repository import MessageRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from utils.safe_logging import redact_sensitive


logger = logging.getLogger("AnalyticsSnapshotService")

ANALYTICS_JOB_TYPE = "analytics_rebuild"
ANALYTICS_JOB_STALE_AFTER = timedelta(minutes=15)
ROMA_TZ = ZoneInfo("Europe/Rome")
PRICE_TOLERANCE = 0.50

TIER_NAMES = ("super_early", "early", "regular", "late")
AGE_BANDS = (
    ("18-20", 18, 20),
    ("21-24", 21, 24),
    ("25-29", 25, 29),
    ("30-34", 30, 34),
    ("35+", 35, 200),
)


class AnalyticsSnapshotService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        message_repository: Optional[MessageRepositoryProtocol] = None,
        job_repository: Optional[JobRepositoryProtocol[AnalyticsJob]] = None,
        entrance_scan_repository: Optional[EntranceScanRepositoryProtocol] = None,
        analytics_snapshot_repository: Optional[AnalyticsSnapshotRepository] = None,
    ):
        self.event_repository = event_repository or EventRepository()
        self.membership_repository = membership_repository or MembershipRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.message_repository = message_repository or MessageRepository()
        self.job_repository = job_repository or AnalyticsJobRepository()
        self.entrance_scan_repository = entrance_scan_repository or EntranceScanRepository()
        self.analytics_snapshot_repository = analytics_snapshot_repository or AnalyticsSnapshotRepository()

    # ---- Public read API -------------------------------------------------
    def get_dashboard_snapshot(self) -> Dict[str, Any]:
        payload = self.analytics_snapshot_repository.get_dashboard_current()
        if payload is None:
            return {"exists": False}
        return {"exists": True, **payload}

    def get_event_snapshot(self, event_id: str) -> Dict[str, Any]:
        payload = self.analytics_snapshot_repository.get_event_snapshot(event_id)
        if payload is None:
            return {"exists": False, "event_id": event_id}
        return {"exists": True, **payload}

    def get_global_snapshot(self) -> Dict[str, Any]:
        payload = self.analytics_snapshot_repository.get_global_current()
        if payload is None:
            return {"exists": False}
        return {"exists": True, **payload}

    def get_events_index(self) -> Dict[str, Any]:
        rows = []
        for event_id, data in self.analytics_snapshot_repository.stream_event_snapshots():
            event_date = self._parse_date_like((data.get("event") or {}).get("date"))
            rows.append(
                {
                    "event_id": event_id,
                    "title": (data.get("event") or {}).get("title") or "Evento",
                    "date": (data.get("event") or {}).get("date"),
                    "start_time": (data.get("event") or {}).get("start_time"),
                    "generated_at": data.get("generated_at"),
                    "sort_date": event_date,
                }
            )

        rows.sort(
            key=lambda row: (
                row.get("sort_date") or date(1970, 1, 1),
                row.get("generated_at") or datetime(1970, 1, 1, tzinfo=timezone.utc),
            ),
            reverse=True,
        )

        for row in rows:
            row.pop("sort_date", None)

        return {"events": rows}

    def get_entrance_flow(self, event_id: str) -> Dict[str, Any]:
        snapshot = self.get_event_snapshot(event_id)
        if snapshot.get("exists"):
            charts = snapshot.get("charts") or {}
            flow = charts.get("entrance_flow") or []
            if flow:
                return {
                    "event_id": event_id,
                    "flow": flow,
                    "source": "snapshot",
                    "generated_at": snapshot.get("generated_at"),
                }

        event = self.event_repository.get_model(event_id)
        if not event:
            return {"event_id": event_id, "flow": [], "source": "missing_event"}

        flow = self._build_entrance_flow(event)
        return {
            "event_id": event_id,
            "flow": flow,
            "source": "live_fallback",
            "generated_at": datetime.now(timezone.utc),
        }

    # ---- Jobs API --------------------------------------------------------
    def enqueue_event_rebuild(self, event_id: str, reason: str = "trigger") -> Dict[str, Any]:
        return self._enqueue_rebuild(scope="event", event_id=event_id, reason=reason)

    def enqueue_global_rebuild(self, reason: str = "trigger") -> Dict[str, Any]:
        return self._enqueue_rebuild(scope="global", reason=reason)

    def enqueue_full_rebuild(self, reason: str = "trigger") -> Dict[str, Any]:
        return self._enqueue_rebuild(scope="all", reason=reason)

    def request_rebuild(
        self,
        scope: str,
        event_id: Optional[str] = None,
        requested_by: str = "admin",
    ) -> Dict[str, Any]:
        normalized_scope = (scope or "").strip().lower()
        if normalized_scope not in {"event", "global", "all"}:
            raise ValueError("scope must be event|global|all")

        if normalized_scope == "event" and not event_id:
            raise ValueError("event_id is required for scope=event")

        reason = f"manual:{requested_by or 'admin'}"
        return self._enqueue_rebuild(
            scope=normalized_scope,
            event_id=event_id,
            reason=reason,
        )

    def process_rebuild_job(self, job_id: str) -> None:
        claimed = self.job_repository.claim_queued(job_id)
        if not claimed:
            logger.info("process_rebuild_job: skip job=%s (not queued)", job_id)
            return

        payload = self.job_repository.get_raw(job_id) or {}
        scope = str(payload.get("scope") or "event").lower()
        event_id = payload.get("target_event_id") or payload.get("event_id")

        try:
            logger.info("process_rebuild_job: start job=%s scope=%s event=%s", job_id, scope, event_id)

            if scope == "event":
                if event_id:
                    self.rebuild_event_snapshot(event_id)
                self.rebuild_global_snapshot()
                self.rebuild_dashboard_snapshot()
            elif scope == "global":
                self.rebuild_global_snapshot()
                self.rebuild_dashboard_snapshot()
            else:
                self.rebuild_all_snapshots()

            self.job_repository.update(
                job_id,
                {
                    "status": "completed",
                    "percent": 100,
                    "finished_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "error": None,
                },
            )
        except Exception as exc:
            logger.error("process_rebuild_job: failed job=%s error=%s", job_id, redact_sensitive(str(exc)))
            self.job_repository.update(
                job_id,
                {
                    "status": "failed",
                    "error": str(exc),
                    "finished_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

    # ---- Snapshot builders ----------------------------------------------
    def rebuild_all_snapshots(self) -> Dict[str, Any]:
        event_ids = []
        for event in self.event_repository.stream_models():
            if event.id:
                event_ids.append(event.id)

        for event_id in event_ids:
            self.rebuild_event_snapshot(event_id)

        self.rebuild_global_snapshot()
        self.rebuild_dashboard_snapshot()
        return {"ok": True, "events_rebuilt": len(event_ids)}

    def rebuild_event_snapshot(self, event_id: str) -> Dict[str, Any]:
        event = self.event_repository.get_model(event_id)
        if not event:
            snapshot = {
                "event_id": event_id,
                "exists": False,
                "generated_at": datetime.now(timezone.utc),
                "charts": {},
            }
            self.analytics_snapshot_repository.set_event_snapshot(event_id, snapshot)
            return snapshot

        participants = self.participant_repository.list(event_id)
        event_purchases = [
            p for p in self.purchase_repository.list_models_by_ref_id(event_id) if self._is_valid_event_purchase(p)
        ]

        total_gross = sum(self._safe_amount(getattr(purchase, "amount_total", 0)) for purchase in event_purchases)
        total_net = sum(self._safe_amount(getattr(purchase, "net_amount", 0)) for purchase in event_purchases)
        total_ticket_count = sum(self._safe_int(getattr(purchase, "participants_count", 0)) for purchase in event_purchases)

        tier_payload = self._build_ticket_tier_payload(event_purchases)
        gender_counts = self._gender_distribution(participants)
        entrance_flow = self._build_entrance_flow(event)

        max_participants = self._safe_int(getattr(event, "max_participants", 0))
        participants_count = len(participants)
        entered_count = self._count_entered(entrance_flow)

        event_snapshot = {
            "event_id": event_id,
            "generated_at": datetime.now(timezone.utc),
            "event": {
                "id": event_id,
                "title": event.title,
                "date": event.date,
                "start_time": event.start_time,
                "max_participants": max_participants,
            },
            "kpis": {
                "participants": participants_count,
                "entered": entered_count,
                "fill_rate": self._percentage(participants_count, max_participants),
                "revenue_gross": round(total_gross, 2),
                "revenue_net": round(total_net, 2),
                "avg_unit_payment": round(total_gross / total_ticket_count, 2) if total_ticket_count > 0 else 0.0,
                "omaggi": sum(
                    1
                    for participant in participants
                    if self._normalize_payment_method(getattr(participant, "payment_method", None)) == "omaggio"
                ),
            },
            "ticket_tiers": tier_payload["tiers"],
            "charts": {
                "entrance_flow": entrance_flow,
                "sales_over_time": self._build_sales_over_time(event_purchases),
                "revenue_by_tier": tier_payload["chart"],
                "event_funnel": self._build_event_funnel(event_purchases, participants_count, entered_count),
                "gender_distribution": self._distribution_rows(gender_counts),
                "membership_trend": self._build_membership_trend(participants),
            },
        }

        self.analytics_snapshot_repository.set_event_snapshot(event_id, event_snapshot)
        return event_snapshot

    def rebuild_global_snapshot(self) -> Dict[str, Any]:
        participants = self._stream_all_participants()
        purchases = [purchase for purchase in self.purchase_repository.stream_models() if self._is_valid_event_purchase(purchase)]

        age_counts = self._age_band_distribution(participants)
        gender_counts = self._gender_distribution(participants)

        omaggi_total = sum(
            1
            for participant in participants
            if self._normalize_payment_method(getattr(participant, "payment_method", None)) == "omaggio"
        )

        gross_total = sum(self._safe_amount(getattr(purchase, "amount_total", 0)) for purchase in purchases)
        ticket_total = sum(self._safe_int(getattr(purchase, "participants_count", 0)) for purchase in purchases)
        avg_unit_payment = gross_total / ticket_total if ticket_total > 0 else 0.0

        global_snapshot = {
            "generated_at": datetime.now(timezone.utc),
            "kpis": {
                "avg_unit_payment": round(avg_unit_payment, 2),
                "omaggi_total": omaggi_total,
                "gender_distribution": gender_counts,
                "age_band_dominant": self._dominant_bucket(age_counts),
            },
            "charts": {
                "age_bands_distribution": [{"band": band, "count": count} for band, count in age_counts.items()],
                "gender_distribution": self._distribution_rows(gender_counts),
                "omaggi_trend_monthly": self._build_omaggi_trend(participants),
                "avg_unit_payment_trend_monthly": self._build_avg_unit_payment_trend(purchases),
            },
        }

        self.analytics_snapshot_repository.set_global_current(global_snapshot)
        return global_snapshot

    def rebuild_dashboard_snapshot(self) -> Dict[str, Any]:
        events = list(self.event_repository.stream_models())
        purchases = [purchase for purchase in self.purchase_repository.stream_models() if self._is_valid_event_purchase(purchase)]
        participants = self._stream_all_participants()

        active_members = sum(
            1 for membership in self.membership_repository.stream() if bool(getattr(membership, "subscription_valid", False))
        )

        event_participants_map = defaultdict(int)
        unique_participant_keys = set()
        for participant in participants:
            event_id = getattr(participant, "event_id", "") or ""
            if event_id:
                event_participants_map[event_id] += 1

            unique_key = (
                (getattr(participant, "membership_id", None) or "").strip().lower()
                or (getattr(participant, "email", None) or "").strip().lower()
                or f"{getattr(participant, 'name', '')}:{getattr(participant, 'surname', '')}:{event_id}"
            )
            if unique_key:
                unique_participant_keys.add(unique_key)

        revenue_net_total = sum(self._safe_amount(getattr(purchase, "net_amount", 0)) for purchase in purchases)
        revenue_net_month = 0.0
        now_local = datetime.now(ROMA_TZ)
        for purchase in purchases:
            ts = self._to_datetime(getattr(purchase, "timestamp", None))
            if not ts:
                continue
            local_ts = ts.astimezone(ROMA_TZ)
            if local_ts.year == now_local.year and local_ts.month == now_local.month:
                revenue_net_month += self._safe_amount(getattr(purchase, "net_amount", 0))

        avg_fill_rate = self._compute_avg_fill_rate(events, event_participants_map)

        global_snapshot = self.get_global_snapshot()
        global_kpis = global_snapshot.get("kpis") if global_snapshot.get("exists") else {}
        gender_distribution = global_kpis.get("gender_distribution") or {"male": 0, "female": 0, "unknown": 0}

        dashboard_snapshot = {
            "generated_at": datetime.now(timezone.utc),
            "kpis": {
                "total_revenue_net": round(revenue_net_total, 2),
                "events": len(events),
                "active_members": active_members,
                "unique_participants": len(unique_participant_keys),
                "avg_fill_rate": round(avg_fill_rate, 2),
                "this_month_revenue": round(revenue_net_month, 2),
            },
            "global_cards": {
                "avg_unit_payment": round(self._safe_amount(global_kpis.get("avg_unit_payment")), 2),
                "omaggi_total": self._safe_int(global_kpis.get("omaggi_total")),
                "gender_split": gender_distribution,
                "age_band_dominant": global_kpis.get("age_band_dominant") or "unknown",
            },
            "upcoming_events": self._build_upcoming_events(events, event_participants_map, purchases),
            "recent_activity": self._build_recent_activity(),
        }

        self.analytics_snapshot_repository.set_dashboard_current(dashboard_snapshot)
        return dashboard_snapshot

    # ---- Internal helpers ------------------------------------------------
    def _enqueue_rebuild(
        self,
        scope: str,
        event_id: Optional[str] = None,
        reason: str = "trigger",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        for doc_id, payload in self.job_repository.stream_raw_by_type(ANALYTICS_JOB_TYPE):
            status = str(payload.get("status") or "").lower()
            if status not in {"queued", "running"}:
                continue

            same_scope = (payload.get("scope") or "") == scope
            same_event = (payload.get("target_event_id") or payload.get("event_id") or "") == (event_id or "")
            matching_job = (scope in {"global", "all"} and same_scope) or (
                scope == "event" and same_scope and same_event
            )
            if not matching_job:
                continue

            if status == "queued":
                self.job_repository.update(
                    doc_id,
                    {
                        "reason": reason,
                        "updated_at": now,
                        "last_kicked_at": now,
                    },
                )
                return {
                    "ok": True,
                    "deduped": True,
                    "kicked": True,
                    "job_id": doc_id,
                    "scope": scope,
                    "event_id": event_id,
                }

            if self._is_stale_job(payload, now):
                self.job_repository.update(
                    doc_id,
                    {
                        "status": "failed",
                        "error": "Stale analytics rebuild job superseded by a new request",
                        "finished_at": now,
                        "updated_at": now,
                    },
                )
                continue

            return {
                "ok": True,
                "deduped": True,
                "kicked": False,
                "job_id": doc_id,
                "scope": scope,
                "event_id": event_id,
            }

        job_model = AnalyticsJob(
            target_event_id=event_id,
            status="queued",
            percent=0,
            scope=scope,
            reason=reason,
            created_at=now,
            updated_at=now,
        )
        job_id = self.job_repository.create_from_model(job_model)

        return {
            "ok": True,
            "deduped": False,
            "kicked": False,
            "job_id": job_id,
            "scope": scope,
            "event_id": event_id,
        }

    def _is_stale_job(self, payload: Dict[str, Any], now: datetime) -> bool:
        status = str(payload.get("status") or "").lower()
        marker = None
        if status == "running":
            marker = self._to_datetime(payload.get("started_at"))
        marker = marker or self._to_datetime(payload.get("updated_at")) or self._to_datetime(payload.get("created_at"))
        if marker is None:
            return True
        return now - marker > ANALYTICS_JOB_STALE_AFTER

    def _stream_all_participants(self) -> List[Any]:
        participants = []
        for participant in self.participant_repository.stream_all():
            participants.append(participant)
        return participants

    def _build_ticket_tier_payload(self, purchases: List[Any]) -> Dict[str, Any]:
        rows = []
        for purchase in purchases:
            participants_count = self._safe_int(getattr(purchase, "participants_count", 0))
            if participants_count <= 0:
                continue
            gross = self._safe_amount(getattr(purchase, "amount_total", 0))
            net = self._safe_amount(getattr(purchase, "net_amount", 0))
            unit_price = gross / participants_count
            rows.append(
                {
                    "purchase_id": getattr(purchase, "id", None),
                    "participants_count": participants_count,
                    "gross": gross,
                    "net": net,
                    "unit_price": unit_price,
                }
            )

        mapping = self._map_ticket_tiers(rows)

        aggregates = {
            tier_name: {"tier": tier_name, "count": 0, "gross": 0.0, "net": 0.0, "avg_unit_price": 0.0}
            for tier_name in TIER_NAMES
        }

        for row in rows:
            tier_name = mapping.get(row["purchase_id"], "regular")
            bucket = aggregates[tier_name]
            bucket["count"] += row["participants_count"]
            bucket["gross"] += row["gross"]
            bucket["net"] += row["net"]

        for tier_name in TIER_NAMES:
            bucket = aggregates[tier_name]
            if bucket["count"] > 0:
                bucket["avg_unit_price"] = round(bucket["gross"] / bucket["count"], 2)
            bucket["gross"] = round(bucket["gross"], 2)
            bucket["net"] = round(bucket["net"], 2)

        tiers = [aggregates[tier_name] for tier_name in TIER_NAMES if aggregates[tier_name]["count"] > 0]
        if not tiers:
            tiers = [{"tier": "regular", "count": 0, "gross": 0.0, "net": 0.0, "avg_unit_price": 0.0}]

        chart = [{"tier": row["tier"], "gross": row["gross"], "net": row["net"]} for row in tiers]

        return {"tiers": tiers, "chart": chart}

    def _map_ticket_tiers(self, rows: List[Dict[str, Any]]) -> Dict[Optional[str], str]:
        if not rows:
            return {}

        clustered = []
        for row in sorted(rows, key=lambda item: item["unit_price"]):
            placed = False
            for cluster in clustered:
                if abs(row["unit_price"] - cluster["center"]) <= PRICE_TOLERANCE:
                    cluster["rows"].append(row)
                    cluster["center"] = sum(item["unit_price"] for item in cluster["rows"]) / len(cluster["rows"])
                    placed = True
                    break
            if not placed:
                clustered.append({"center": row["unit_price"], "rows": [row]})

        clustered.sort(key=lambda cluster: cluster["center"])
        cluster_count = len(clustered)

        cluster_to_tier = {}
        if cluster_count <= 1:
            for index in range(cluster_count):
                cluster_to_tier[index] = "regular"
        elif cluster_count == 2:
            cluster_to_tier[0] = "early"
            cluster_to_tier[1] = "regular"
        elif cluster_count == 3:
            cluster_to_tier[0] = "early"
            cluster_to_tier[1] = "regular"
            cluster_to_tier[2] = "late"
        else:
            for index in range(cluster_count):
                if index == 0:
                    cluster_to_tier[index] = "super_early"
                elif index == 1:
                    cluster_to_tier[index] = "early"
                elif index == cluster_count - 1:
                    cluster_to_tier[index] = "late"
                else:
                    cluster_to_tier[index] = "regular"

        mapping = {}
        for index, cluster in enumerate(clustered):
            tier = cluster_to_tier.get(index, "regular")
            for row in cluster["rows"]:
                mapping[row.get("purchase_id")] = tier
        return mapping

    def _build_sales_over_time(self, purchases: List[Any]) -> List[Dict[str, Any]]:
        by_day = defaultdict(lambda: {"gross": 0.0, "net": 0.0})
        for purchase in purchases:
            ts = self._to_datetime(getattr(purchase, "timestamp", None))
            if not ts:
                continue
            day = ts.astimezone(ROMA_TZ).strftime("%Y-%m-%d")
            by_day[day]["gross"] += self._safe_amount(getattr(purchase, "amount_total", 0))
            by_day[day]["net"] += self._safe_amount(getattr(purchase, "net_amount", 0))

        rows = []
        for day in sorted(by_day.keys()):
            rows.append(
                {
                    "day": day,
                    "gross": round(by_day[day]["gross"], 2),
                    "net": round(by_day[day]["net"], 2),
                }
            )
        return rows[-120:]

    def _build_event_funnel(self, purchases: List[Any], participants_count: int, entered_count: int) -> List[Dict[str, Any]]:
        ticket_count = sum(self._safe_int(getattr(purchase, "participants_count", 0)) for purchase in purchases)
        return [
            {"stage": "Acquisti", "value": len(purchases)},
            {"stage": "Ticket", "value": ticket_count},
            {"stage": "Partecipanti", "value": participants_count},
            {"stage": "Ingressi", "value": entered_count},
        ]

    def _build_membership_trend(self, participants: List[Any]) -> List[Dict[str, Any]]:
        by_day = defaultdict(lambda: {"with_membership": 0, "without_membership": 0})

        for participant in participants:
            created_at = self._to_datetime(getattr(participant, "created_at", None) or getattr(participant, "createdAt", None))
            key = created_at.astimezone(ROMA_TZ).strftime("%Y-%m-%d") if created_at else "unknown"

            membership_id = (getattr(participant, "membership_id", None) or getattr(participant, "membershipId", None) or "")
            if membership_id:
                by_day[key]["with_membership"] += 1
            else:
                by_day[key]["without_membership"] += 1

        cumulative_with = 0
        cumulative_without = 0
        rows = []
        for day in sorted(by_day.keys()):
            if day == "unknown":
                continue
            cumulative_with += by_day[day]["with_membership"]
            cumulative_without += by_day[day]["without_membership"]
            rows.append(
                {
                    "day": day,
                    "with_membership": cumulative_with,
                    "without_membership": cumulative_without,
                }
            )

        return rows[-120:]

    def _build_entrance_flow(self, event) -> List[Dict[str, Any]]:
        event_date = self._parse_date_like(getattr(event, "date", None))
        if not event_date:
            event_date = datetime.now(ROMA_TZ).date()

        window_start = datetime.combine(event_date, time(22, 0), tzinfo=ROMA_TZ)
        window_end = window_start + timedelta(hours=8)

        total_buckets = int((window_end - window_start).total_seconds() // (30 * 60))
        counts = [0 for _ in range(total_buckets)]

        event_id = getattr(event, "id", None)
        scans = self.entrance_scan_repository.list(event_id) if event_id else []
        for scan in scans:
            scanned_at = self._to_datetime(getattr(scan, "scanned_at", None))
            if not scanned_at:
                continue
            local_ts = scanned_at.astimezone(ROMA_TZ)
            if not (window_start <= local_ts < window_end):
                continue

            index = int((local_ts - window_start).total_seconds() // (30 * 60))
            if 0 <= index < total_buckets:
                counts[index] += 1

        output = []
        cumulative = 0
        for index in range(total_buckets):
            bucket_start = window_start + timedelta(minutes=30 * index)
            bucket_end = bucket_start + timedelta(minutes=30)
            count = counts[index]
            cumulative += count
            output.append(
                {
                    "bucket_start": bucket_start.isoformat(),
                    "bucket_end": bucket_end.isoformat(),
                    "label": f"{bucket_start.strftime('%H:%M')} - {bucket_end.strftime('%H:%M')}",
                    "count": count,
                    "cumulative": cumulative,
                }
            )

        return output

    def _build_omaggi_trend(self, participants: List[Any]) -> List[Dict[str, Any]]:
        months = defaultdict(int)
        for participant in participants:
            if self._normalize_payment_method(getattr(participant, "payment_method", None)) != "omaggio":
                continue

            created_at = self._to_datetime(getattr(participant, "created_at", None) or getattr(participant, "createdAt", None))
            if not created_at:
                continue
            month = created_at.astimezone(ROMA_TZ).strftime("%Y-%m")
            months[month] += 1

        rows = [{"month": month, "count": months[month]} for month in sorted(months.keys())]
        return rows[-18:]

    def _build_avg_unit_payment_trend(self, purchases: List[Any]) -> List[Dict[str, Any]]:
        month_totals = defaultdict(lambda: {"amount": 0.0, "participants": 0})

        for purchase in purchases:
            ts = self._to_datetime(getattr(purchase, "timestamp", None))
            if not ts:
                continue
            month = ts.astimezone(ROMA_TZ).strftime("%Y-%m")
            month_totals[month]["amount"] += self._safe_amount(getattr(purchase, "amount_total", 0))
            month_totals[month]["participants"] += self._safe_int(getattr(purchase, "participants_count", 0))

        rows = []
        for month in sorted(month_totals.keys()):
            total_participants = month_totals[month]["participants"]
            avg = month_totals[month]["amount"] / total_participants if total_participants > 0 else 0.0
            rows.append({"month": month, "value": round(avg, 2)})

        return rows[-18:]

    def _build_upcoming_events(self, events, participants_map: Dict[str, int], purchases: List[Any]) -> List[Dict[str, Any]]:
        today = datetime.now(ROMA_TZ).date()
        revenues = defaultdict(float)
        for purchase in purchases:
            event_id = getattr(purchase, "ref_id", None)
            if not event_id:
                continue
            revenues[event_id] += self._safe_amount(getattr(purchase, "net_amount", 0))

        candidates = []
        for event in events:
            if not event.id:
                continue
            event_date = self._parse_date_like(event.date)
            if not event_date or event_date < today:
                continue

            max_participants = self._safe_int(getattr(event, "max_participants", 0))
            participants_count = participants_map.get(event.id, 0)
            candidates.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "date": event.date,
                    "start_time": event.start_time,
                    "participants": participants_count,
                    "max_participants": max_participants,
                    "fill_rate": self._percentage(participants_count, max_participants),
                    "revenue_net": round(revenues.get(event.id, 0.0), 2),
                    "sort_date": event_date,
                }
            )

        candidates.sort(key=lambda row: row["sort_date"])
        rows = candidates[:3]
        for row in rows:
            row.pop("sort_date", None)
        return rows

    def _build_recent_activity(self) -> List[Dict[str, Any]]:
        activity = []

        purchases = sorted(
            list(self.purchase_repository.stream_models()),
            key=lambda item: self._to_datetime(getattr(item, "timestamp", None)) or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
        for purchase in purchases[:4]:
            activity.append(
                {
                    "id": getattr(purchase, "id", None),
                    "type": "purchase",
                    "title": "Nuovo acquisto",
                    "subtitle": f"{getattr(purchase, 'payer_name', '')} {getattr(purchase, 'payer_surname', '')}".strip() or "Acquisto",
                    "amount": round(self._safe_amount(getattr(purchase, "amount_total", 0)), 2),
                    "timestamp": self._to_datetime(getattr(purchase, "timestamp", None)),
                }
            )

        participants = sorted(
            self._stream_all_participants(),
            key=lambda item: self._to_datetime(getattr(item, "created_at", None) or getattr(item, "createdAt", None))
            or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
        for participant in participants[:3]:
            activity.append(
                {
                    "id": getattr(participant, "id", None),
                    "type": "participant",
                    "title": "Nuovo partecipante",
                    "subtitle": f"{getattr(participant, 'name', '')} {getattr(participant, 'surname', '')}".strip() or "Partecipante",
                    "timestamp": self._to_datetime(getattr(participant, "created_at", None) or getattr(participant, "createdAt", None)),
                }
            )

        memberships = sorted(
            list(self.membership_repository.stream()),
            key=lambda item: self._to_datetime(getattr(item, "start_date", None)) or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
        for membership in memberships[:2]:
            activity.append(
                {
                    "id": getattr(membership, "id", None),
                    "type": "membership",
                    "title": "Nuova tessera",
                    "subtitle": f"{getattr(membership, 'name', '')} {getattr(membership, 'surname', '')}".strip() or "Membership",
                    "timestamp": self._to_datetime(getattr(membership, "start_date", None)),
                }
            )

        messages = sorted(
            list(self.message_repository.stream()),
            key=lambda item: self._to_datetime(getattr(item, "timestamp", None)) or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
        for message in messages[:2]:
            activity.append(
                {
                    "id": getattr(message, "id", None),
                    "type": "message",
                    "title": "Nuovo messaggio",
                    "subtitle": getattr(message, "name", None) or getattr(message, "email", None) or "Contatto",
                    "timestamp": self._to_datetime(getattr(message, "timestamp", None)),
                }
            )

        activity.sort(
            key=lambda row: row.get("timestamp") or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )

        output = []
        for row in activity[:10]:
            ts = row.get("timestamp")
            output.append(
                {
                    **{key: value for key, value in row.items() if key != "timestamp"},
                    "timestamp": ts.isoformat() if isinstance(ts, datetime) else None,
                }
            )
        return output

    def _compute_avg_fill_rate(self, events, participants_map: Dict[str, int]) -> float:
        rates = []
        for event in events:
            max_participants = self._safe_int(getattr(event, "max_participants", 0))
            if max_participants <= 0:
                continue
            count = participants_map.get(event.id or "", 0)
            rates.append((count / max_participants) * 100)

        if not rates:
            return 0.0
        return sum(rates) / len(rates)

    def _age_band_distribution(self, participants: List[Any]) -> Dict[str, int]:
        output = {band: 0 for band, _, _ in AGE_BANDS}
        output["unknown"] = 0

        for participant in participants:
            age = self._age_from_birthdate(getattr(participant, "birthdate", None))
            if age is None:
                output["unknown"] += 1
                continue

            matched = False
            for band, start, end in AGE_BANDS:
                if start <= age <= end:
                    output[band] += 1
                    matched = True
                    break

            if not matched:
                output["unknown"] += 1

        return output

    def _gender_distribution(self, participants: List[Any]) -> Dict[str, int]:
        output = {"male": 0, "female": 0, "unknown": 0}
        for participant in participants:
            key = self._normalize_gender(getattr(participant, "gender", None))
            output[key] += 1
        return output

    def _distribution_rows(self, payload: Dict[str, int]) -> List[Dict[str, Any]]:
        return [
            {"key": "male", "count": self._safe_int(payload.get("male", 0))},
            {"key": "female", "count": self._safe_int(payload.get("female", 0))},
            {"key": "unknown", "count": self._safe_int(payload.get("unknown", 0))},
        ]

    def _dominant_bucket(self, payload: Dict[str, int]) -> str:
        if not payload:
            return "unknown"
        return max(payload.items(), key=lambda item: item[1])[0]

    def _count_entered(self, entrance_flow: List[Dict[str, Any]]) -> int:
        return sum(self._safe_int(bucket.get("count")) for bucket in entrance_flow)

    _VALID_EVENT_TYPE_VALUES = {PurchaseTypes.EVENT.value, "event_and_membership"}

    def _is_valid_event_purchase(self, purchase: Any) -> bool:
        purchase_type = getattr(purchase, "purchase_type", None)
        purchase_type_value = str(getattr(purchase_type, "value", purchase_type or "")).lower()
        if purchase_type_value not in self._VALID_EVENT_TYPE_VALUES:
            return False

        event_id = getattr(purchase, "ref_id", None)
        if not event_id:
            return False

        participants_count = self._safe_int(getattr(purchase, "participants_count", 0))
        if participants_count <= 0:
            return False

        status = str(getattr(purchase, "status", "") or "").upper()
        capture_status = str(getattr(purchase, "capture_status", "") or "").upper()
        if status in PurchaseStatus.invalid_statuses() or capture_status in PurchaseStatus.invalid_statuses():
            return False

        return True

    def _normalize_payment_method(self, value: Any) -> str:
        raw = getattr(value, "value", value)
        return str(raw or "unknown").strip().lower()

    def _normalize_gender(self, value: Any) -> str:
        raw = str(value or "").strip().lower()
        if raw in {"male", "maschio", "m"}:
            return "male"
        if raw in {"female", "femmina", "f"}:
            return "female"
        return "unknown"

    def _age_from_birthdate(self, value: Any) -> Optional[int]:
        if value is None:
            return None

        if isinstance(value, datetime):
            birth_date = value.date()
        elif isinstance(value, date):
            birth_date = value
        elif isinstance(value, str):
            birth_date = self._parse_date_like(value)
            if not birth_date:
                dt = self._to_datetime(value)
                birth_date = dt.date() if dt else None
        else:
            return None

        if not birth_date:
            return None

        today = datetime.now(ROMA_TZ).date()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        if age < 0 or age > 120:
            return None
        return age

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

        parsed_event = parse_event_date(raw)
        if parsed_event:
            return parsed_event

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
                if dt and dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None

        if isinstance(value, (int, float)):
            try:
                as_seconds = value / 1000.0 if value > 1e12 else value
                return datetime.fromtimestamp(as_seconds, tz=timezone.utc)
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

    def _percentage(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)
