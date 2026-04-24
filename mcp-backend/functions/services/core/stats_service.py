from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from dto import PurchaseDTO
from interfaces.repositories import (
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    MessageRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.message_repository import MessageRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository


class StatsService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        message_repository: Optional[MessageRepositoryProtocol] = None,
    ):
        self.event_repository = event_repository or EventRepository()
        self.membership_repository = membership_repository or MembershipRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self.message_repository = message_repository or MessageRepository()

    def get_general_stats(self):
        total_active_members = sum(
            1 for member in self.membership_repository.stream() if member.subscription_valid
        )

        purchases = list(self.purchase_repository.stream_models())
        total_purchases = len(purchases)
        total_gross_amount = sum(self._safe_amount(p.amount_total) for p in purchases)
        total_net_amount = sum(self._safe_amount(p.net_amount) for p in purchases)

        total_events = sum(1 for _ in self.event_repository.stream_models())

        upcoming_event = self._get_upcoming_event_model()
        upcoming_event_participants = 0
        upcoming_event_total_paid = 0.0
        if upcoming_event and upcoming_event.id:
            participants = self.participant_repository.list(upcoming_event.id)
            for participant in participants:
                upcoming_event_participants += 1
                upcoming_event_total_paid += self._safe_amount(participant.price)

        now = datetime.now(timezone.utc)
        time_limit = now - timedelta(hours=24)
        last_24h_unanswered = self.message_repository.count_unanswered_since(time_limit)

        last_message = self._message_payload(self.message_repository.get_last_dto())
        last_membership = self._membership_payload(self.membership_repository.get_last_by_start_date())
        last_purchase = self._purchase_payload(self.purchase_repository.get_last_by_timestamp())
        last_participant = self._participant_payload(self.participant_repository.get_last_across_events())

        response = {
            "total_active_members": total_active_members,
            "total_purchases": total_purchases,
            "total_events": total_events,
            "upcoming_event_participants": upcoming_event_participants,
            "upcoming_event_total_paid": f"{upcoming_event_total_paid:.2f}",
            "total_gross_amount": f"{total_gross_amount:.2f}",
            "total_net_amount": f"{total_net_amount:.2f}",
            "last_membership": last_membership,
            "last_purchase": last_purchase,
            "last_participant": last_participant,
            "last_24h_unanswered_messages": last_24h_unanswered,
            "last_message": last_message,
        }

        return response

    def _safe_amount(self, value: Optional[Any]) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _message_payload(self, dto) -> Optional[Dict[str, Any]]:
        if not dto:
            return None
        return dto.to_payload()

    def _membership_payload(self, dto) -> Optional[Dict[str, Any]]:
        if not dto:
            return None
        return dto.to_payload()

    def _purchase_payload(self, model) -> Optional[Dict[str, Any]]:
        if not model:
            return None
        payload = PurchaseDTO.from_model(model).to_payload()
        payload["id"] = model.id
        return payload

    def _participant_payload(self, dto) -> Optional[Dict[str, Any]]:
        if not dto:
            return None
        return dto.to_payload()

    def _safe_parse_date(self, date_str: str):
        if not date_str:
            return None
        value = str(date_str).strip()
        for fmt in ["%d-%m-%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _get_upcoming_event_model(self):
        candidates = []
        for model in self.event_repository.stream_models():
            if not model.date:
                continue
            event_date = self._safe_parse_date(model.date)
            if not event_date:
                continue
            if event_date >= datetime.now().date():
                candidates.append((event_date, model))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]
