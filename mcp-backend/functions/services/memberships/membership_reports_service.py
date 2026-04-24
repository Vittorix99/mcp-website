import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from dto import MembershipDTO, PurchaseDTO
from interfaces.repositories import (
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    MembershipSettingsRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from errors.service_errors import NotFoundError, ValidationError


class MembershipReportsService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        settings_repository: Optional[MembershipSettingsRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
    ):
        self.logger = logging.getLogger("MembershipReportsService")
        self.event_repository = event_repository or EventRepository()
        self.membership_repository = membership_repository or MembershipRepository()
        self.settings_repository = settings_repository or MembershipSettingsRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()

    def _parse_iso_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed
        except ValueError:
            return None

    def _parse_amount(self, value):
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _safe_divide_amount(self, amount, count):
        if amount is None or not count:
            return None
        return amount / count

    def _chunked(self, items, size=10):
        if not items:
            return
        for i in range(0, len(items), size):
            yield items[i:i + size]

    def get_memberships_report(self, event_id: str) -> Dict[str, Any]:
        if not event_id:
            raise ValidationError("Missing event_id")

        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")

        year = str(datetime.now().year)
        membership_fee = self._parse_amount(self.settings_repository.get_price_by_year(year))

        purchases: Dict[str, Dict[str, Any]] = {}
        total_net_collected = 0.0
        for purchase in self.purchase_repository.list_models_by_ref_id(event_id):
            purchase_id = purchase.id
            if not purchase_id:
                continue
            purchase_payload = PurchaseDTO.from_model(purchase).to_payload()
            purchase_payload["id"] = purchase_id
            purchases[purchase_id] = purchase_payload
            net_amount = self._parse_amount(purchase_payload.get("net_amount")) or 0.0
            total_net_collected += net_amount
        self.logger.info(
            "[get_memberships_report] event_id=%s purchases=%s",
            event_id,
            len(purchases),
        )

        memberships_by_purchase: Dict[str, List[Dict[str, Any]]] = {}
        membership_cache: Dict[str, Dict[str, Any]] = {}
        new_member_ids = set()

        purchase_ids = list(purchases.keys())
        for batch in self._chunked(purchase_ids, 10):
            for membership in self.membership_repository.list_by_purchase_ids(batch):
                m_data = MembershipDTO.from_model(membership).to_payload()
                purchase_id = membership.purchase_id
                if purchase_id:
                    memberships_by_purchase.setdefault(purchase_id, []).append(m_data)
                membership_cache[membership.id] = m_data
                new_member_ids.add(membership.id)

        rows: List[Dict[str, Any]] = []

        participants_by_purchase: Dict[str, List[str]] = {}
        participant_membership_ids = set()
        for participant in self.participant_repository.stream(event_id):
            membership_id = participant.membership_id
            purchase_id = participant.purchase_id
            if not membership_id or not purchase_id:
                continue
            participants_by_purchase.setdefault(purchase_id, []).append(membership_id)
            participant_membership_ids.add(membership_id)
        self.logger.info(
            "[get_memberships_report] participants=%s participants_purchases=%s",
            len(participant_membership_ids),
            len(participants_by_purchase),
        )

        missing_member_ids = [
            mid for mid in participant_membership_ids if mid not in membership_cache
        ]
        for batch in self._chunked(missing_member_ids, 10):
            for membership in self.membership_repository.list_by_ids(batch):
                membership_cache[membership.id] = MembershipDTO.from_model(membership).to_payload()

        for purchase_id, members in memberships_by_purchase.items():
            purchase = purchases.get(purchase_id, {})
            net_amount = self._parse_amount(purchase.get("net_amount"))
            participants = participants_by_purchase.get(purchase_id)
            total_participants = len(participants) if participants else len(members)
            net_per_member = self._safe_divide_amount(net_amount, total_participants)

            for member in members:
                quota_variabile = net_per_member
                if net_per_member is not None and membership_fee is not None:
                    quota_variabile = net_per_member - membership_fee

                rows.append({
                    "data_iscrizione": member.get("start_date"),
                    "name": member.get("name", ""),
                    "surname": member.get("surname", ""),
                    "email": member.get("email", ""),
                    "associato": "Si",
                    "netto_pagato": net_per_member,
                    "quota_variabile": quota_variabile,
                })

        existing_associates_count = 0
        for purchase_id, membership_ids in participants_by_purchase.items():
            purchase = purchases.get(purchase_id, {})
            net_amount = self._parse_amount(purchase.get("net_amount"))
            net_per_participant = self._safe_divide_amount(net_amount, len(membership_ids))

            for membership_id in membership_ids:
                if membership_id in new_member_ids:
                    continue
                member = membership_cache.get(membership_id)
                if not member:
                    continue

                rows.append({
                    "data_iscrizione": member.get("start_date"),
                    "name": member.get("name", ""),
                    "surname": member.get("surname", ""),
                    "email": member.get("email", ""),
                    "associato": "No",
                    "netto_pagato": net_per_participant,
                    "quota_variabile": net_per_participant,
                })
                existing_associates_count += 1

        rows.sort(
            key=lambda r: self._parse_iso_date(r.get("data_iscrizione")) or datetime.max
        )

        response = {
            "event_id": event_id,
            "new_associates_count": len(new_member_ids),
            "existing_associates_count": existing_associates_count,
            "total_net_collected": total_net_collected,
            "rows": rows,
        }
        self.logger.info(
            "[get_memberships_report] rows=%s new_associates=%s",
            len(rows),
            len(new_member_ids),
        )
        return response
