from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Protocol

from models import (
    AdminUser,
    ContactMessage,
    EntranceScan,
    Event,
    EventOrder,
    EventParticipant,
    Job,
    Membership,
    NewsletterConsent,
    NewsletterParticipant,
    NewsletterSignup,
    Purchase,
    Setting,
    UserProfile,
)
from models.scan_token import ScanToken


class AdminRepositoryProtocol(Protocol):
    def list_models(self) -> List[AdminUser]:
        ...

    def get(self, admin_id: str) -> Optional[AdminUser]:
        ...

    def create_with_id(self, admin_id: str, admin_user: AdminUser) -> None:
        ...

    def update_from_model(self, admin_id: str, admin_user: AdminUser) -> None:
        ...

    def delete(self, admin_id: str) -> None:
        ...


class AdminAuthRepositoryProtocol(Protocol):
    def create_admin_user(self, email: str, password: str, display_name: str = "") -> str:
        ...

    def set_admin_claims(self, admin_id: str) -> None:
        ...

    def update_admin_user(
        self,
        admin_id: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> None:
        ...

    def delete_admin_user(self, admin_id: str) -> None:
        ...


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
    def get(self, membership_id: str) -> Optional[Membership]:
        ...

    def list(self) -> List[Membership]:
        ...

    def stream(self) -> Iterable[Membership]:
        ...

    def get_last_by_start_date(self) -> Optional[Membership]:
        ...

    def get_model_by_slug(self, slug: str) -> Optional[Membership]:
        ...

    def find_by_email(self, email: str) -> Optional[Membership]:
        ...

    def find_by_phone(self, phone: str) -> Optional[Membership]:
        ...

    def create(self, membership: Membership) -> str:
        ...

    def create_from_model(self, membership: Membership) -> str:
        ...

    def update_from_model(self, membership_id: str, payload: Membership) -> bool:
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

    def get_wallet_model(self) -> Optional[str]:
        ...

    def set_wallet_model(self, model_id: str) -> None:
        ...


class ParticipantRepositoryProtocol(Protocol):
    def list(self, event_id: str) -> List[EventParticipant]:
        ...

    def stream(self, event_id: str) -> Iterable[EventParticipant]:
        ...

    def get(self, event_id: str, participant_id: str) -> Optional[EventParticipant]:
        ...

    def create_from_model(self, event_id: str, participant: EventParticipant) -> str:
        ...

    def update_from_model(self, event_id: str, participant_id: str, participant: EventParticipant) -> bool:
        ...

    def delete(self, event_id: str, participant_id: str) -> None:
        ...

    def count(self, event_id: str) -> int:
        ...

    def any_with_contacts(self, event_id: str, emails: List[str], phones: List[str]) -> bool:
        ...

    def get_last_across_events(self) -> Optional[EventParticipant]:
        ...

    def set_membership(self, event_id: str, participant_id: str, membership_id: Optional[str]) -> None:
        ...

    def clear_membership_reference(self, membership_id: str) -> int:
        ...

    def get_by_membership_id(self, event_id: str, membership_id: str) -> Optional[EventParticipant]:
        ...

    def update_membership_reference(self, old_membership_id: str, new_membership_id: str) -> int:
        ...

    def update_entered(self, event_id: str, participant_id: str, entered: bool) -> None:
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
    def list_models_ordered_by_name(self) -> List[ContactMessage]:
        ...

    def count_unanswered_since(self, time_limit: Any) -> int:
        ...

    def get_last_model(self) -> Optional[ContactMessage]:
        ...

    def get_model(self, message_id: str) -> Optional[ContactMessage]:
        ...

    def create_from_model(self, payload: ContactMessage) -> str:
        ...

    def delete(self, message_id: str) -> None:
        ...

    def update_from_model(self, message_id: str, payload: ContactMessage) -> None:
        ...


class SettingsRepositoryProtocol(Protocol):
    def get(self, key: str) -> Optional[Setting]:
        ...

    def save(self, key: str, value: Any) -> Setting:
        ...

    def list(self) -> List[Setting]:
        ...


class OrderRepositoryProtocol(Protocol):
    def save(self, order_id: str, order: EventOrder) -> None:
        ...

    def get_model(self, order_id: str) -> Optional[EventOrder]:
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

    def update(self, job_id: str, payload: Dict[str, Any]) -> None:
        ...

    def update_from_model(self, job_id: str, job: Job) -> None:
        ...


class UserRepositoryProtocol(Protocol):
    def get_by_id(self, user_id: str) -> Optional[UserProfile]:
        ...


class NewsletterRepositoryProtocol(Protocol):
    def stream_signups(self) -> Iterable[NewsletterSignup]:
        ...

    def stream_consents(self) -> Iterable[NewsletterConsent]:
        ...

    def get_signup(self, signup_id: str) -> Optional[NewsletterSignup]:
        ...

    def find_signup_by_email(self, email: str) -> Optional[NewsletterSignup]:
        ...

    def add_signup_from_model(self, signup: NewsletterSignup) -> str:
        ...

    def update_signup_from_model(self, signup_id: str, signup: NewsletterSignup) -> None:
        ...

    def delete_signup(self, signup_id: str) -> None:
        ...

    def unsubscribe_by_email(self, email: str) -> None:
        ...

    def add_participants_batch(self, participants: List[NewsletterParticipant]) -> None:
        ...


class ScanTokenRepositoryProtocol(Protocol):
    def get(self, token: str) -> Optional[ScanToken]:
        ...

    def create(self, token: str, event_id: str, admin_uid: str, expires_at: Any) -> None:
        ...

    def deactivate(self, token: str, admin_uid: str) -> None:
        ...


class EntranceScanRepositoryProtocol(Protocol):
    def get(self, event_id: str, membership_id: str) -> Optional[EntranceScan]:
        ...

    def exists(self, event_id: str, membership_id: str) -> bool:
        ...

    def create_scan(self, event_id: str, membership_id: str, scan_token: str) -> Optional[EntranceScan]:
        ...

    def create_manual(self, event_id: str, membership_id: str, admin_uid: str) -> None:
        ...

    def delete(self, event_id: str, membership_id: str) -> None:
        ...

    def count(self, event_id: str) -> int:
        ...
