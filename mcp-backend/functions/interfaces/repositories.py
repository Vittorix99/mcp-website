from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Protocol, Union

from dto import ContactMessageDTO, EventParticipantDTO, JobDTO, MembershipDTO, SettingDTO
from dto.error_log import ErrorLogDTO
from models import (
    ContactMessage,
    ErrorLog,
    Event,
    EventOrder,
    EventParticipant,
    Job,
    Membership,
    Purchase,
    Setting,
)


class EventRepositoryProtocol(Protocol):
    def stream_models(self) -> Iterable[Event]:
        ...

    def get_model(self, event_id: str) -> Optional[Event]:
        ...

    def get_model_by_slug(self, slug: str) -> Optional[Event]:
        ...

    def create_from_model(self, event: Event, slug_seed: str) -> str:
        ...

    def update_from_model(self, event_id: str, event: Event) -> None:
        ...

    def delete(self, event_id: str) -> None:
        ...


class MembershipRepositoryProtocol(Protocol):
    def get_all(self) -> List[MembershipDTO]:
        ...

    def get(self, membership_id: str) -> Optional[Membership]:
        ...

    def list(self) -> List[Membership]:
        ...

    def stream(self) -> Iterable[MembershipDTO]:
        ...

    def get_last_by_start_date(self) -> Optional[MembershipDTO]:
        ...

    def get_model_by_slug(self, slug: str) -> Optional[Membership]:
        ...

    def find_by_email(self, email: str) -> Optional[Membership]:
        ...

    def find_by_phone(self, phone: str) -> Optional[Membership]:
        ...

    def create(self, payload: Union[Dict[str, Any], MembershipDTO, Membership]) -> str:
        ...

    def create_from_model(self, membership: Membership) -> str:
        ...

    def update_fields(self, membership_id: str, payload: Dict[str, Any]) -> bool:
        ...

    def update_from_model(self, membership_id: str, payload: Union[Membership, MembershipDTO]) -> bool:
        ...

    def delete(self, membership_id: str) -> None:
        ...

    def append_purchase(self, membership_id: str, purchase_id: str) -> bool:
        ...

    def add_attended_event(self, membership_id: str, event_id: str) -> bool:
        ...

    def add_attended_event_and_purchase(self, membership_id: str, event_id: str, purchase_id: str) -> bool:
        ...

    def find_by_year(self, year: int) -> List[Membership]:
        ...

    def add_renewal(self, membership_id: str, renewal_dict: Dict[str, Any]) -> bool:
        ...

    def list_by_purchase_ids(self, purchase_ids: List[str]) -> Iterable[Membership]:
        ...

    def list_by_ids(self, membership_ids: List[str]) -> Iterable[Membership]:
        ...

    def clear_wallet(self, membership_id: str) -> None:
        ...

    def set_wallet(self, membership_id: str, pass_id: str, wallet_url: str) -> None:
        ...

    def set_merging(self, membership_id: str, value: Optional[bool]) -> None:
        ...


class MembershipSettingsRepositoryProtocol(Protocol):
    def set_price_by_year(self, year: str, price: float) -> None:
        ...

    def get_price_by_year(self, year: str) -> Optional[float]:
        ...


class ParticipantRepositoryProtocol(Protocol):
    def list(self, event_id: str) -> List[EventParticipantDTO]:
        ...

    def stream(self, event_id: str) -> Iterable[EventParticipantDTO]:
        ...

    def get(self, event_id: str, participant_id: str) -> Optional[EventParticipantDTO]:
        ...

    def create(self, event_id: str, payload: Union[Dict[str, Any], EventParticipantDTO]) -> str:
        ...

    def create_from_model(self, event_id: str, participant: EventParticipant) -> str:
        ...

    def update(self, event_id: str, participant_id: str, payload: Union[Dict[str, Any], EventParticipantDTO]) -> bool:
        ...

    def delete(self, event_id: str, participant_id: str) -> None:
        ...

    def count(self, event_id: str) -> int:
        ...

    def any_with_contacts(self, event_id: str, emails: List[str], phones: List[str]) -> bool:
        ...

    def get_last_across_events(self) -> Optional[EventParticipantDTO]:
        ...

    def set_membership(self, event_id: str, participant_id: str, membership_id: Optional[str]) -> None:
        ...

    def clear_membership_reference(self, membership_id: str) -> int:
        ...

    def update_membership_reference(self, old_membership_id: str, new_membership_id: str) -> int:
        ...


class PurchaseRepositoryProtocol(Protocol):
    def create(self, purchase: Purchase) -> str:
        ...

    def create_from_model(self, purchase: Purchase) -> str:
        ...

    def update_participants(self, purchase_id: str, participants_count: int, membership_ids: List[str]) -> None:
        ...

    def stream_models(self) -> Iterable[Purchase]:
        ...

    def get_model(self, purchase_id: str) -> Optional[Purchase]:
        ...

    def get_model_by_slug(self, slug: str) -> Optional[Purchase]:
        ...

    def get_last_by_timestamp(self) -> Optional[Purchase]:
        ...

    def list_models_by_ref_id(self, event_id: str) -> Iterable[Purchase]:
        ...

    def delete(self, purchase_id: str) -> bool:
        ...


class MessageRepositoryProtocol(Protocol):
    def list_ordered_by_name(self) -> List[ContactMessageDTO]:
        ...

    def count_unanswered_since(self, time_limit: Any) -> int:
        ...

    def get_last_dto(self) -> Optional[ContactMessageDTO]:
        ...

    def get(self, message_id: str) -> Optional[ContactMessageDTO]:
        ...

    def create_from_model(self, payload: ContactMessage) -> str:
        ...

    def delete(self, message_id: str) -> None:
        ...

    def update(self, message_id: str, payload: Union[Dict[str, Any], ContactMessageDTO, ContactMessage]) -> None:
        ...


class SettingsRepositoryProtocol(Protocol):
    def get_dto(self, key: str) -> Optional[SettingDTO]:
        ...

    def save(self, key: str, value: Any) -> Setting:
        ...

    def list_dtos(self) -> List[SettingDTO]:
        ...


class OrderRepositoryProtocol(Protocol):
    def save(self, order_id: str, order: EventOrder) -> None:
        ...

    def get(self, order_id: str) -> Optional[Dict[str, Any]]:
        ...

    def delete(self, order_id: str) -> None:
        ...

    def update_status(self, order_id: str, status: str) -> None:
        ...

    def mark_captured(self, order_id: str, payment_method: str) -> None:
        ...

    def set_purchase_id(self, order_id: str, purchase_id: str) -> None:
        ...


class JobRepositoryProtocol(Protocol):
    def create_from_model(self, job: Job) -> str:
        ...

    def get_model(self, job_id: str) -> Optional[Job]:
        ...

    def update_from_model(self, job_id: str, payload: Union[JobDTO, Job]) -> None:
        ...


class ErrorLogRepositoryProtocol(Protocol):
    def list_dtos(
        self,
        limit: int = 100,
        service: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[ErrorLogDTO]:
        ...

    def get_dto(self, error_log_id: str) -> Optional[ErrorLogDTO]:
        ...

    def create_from_dto(self, dto: ErrorLogDTO) -> str:
        ...

    def update_from_payload(self, error_log_id: str, payload: Dict[str, Any]) -> bool:
        ...

    def get_model(self, error_log_id: str) -> Optional[ErrorLog]:
        ...

    def delete(self, error_log_id: str) -> None:
        ...


class UserRepositoryProtocol(Protocol):
    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        ...
