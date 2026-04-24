"""Repository helpers for Firestore persistence."""

from .base import BaseRepository
from .entrance_scan_repository import EntranceScanRepository
from .event_repository import EventRepository
from .job_repository import JobRepository
from interfaces.repositories import (
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    MembershipSettingsRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from .membership_repository import MembershipRepository
from .message_repository import MessageRepository
from .newsletter_repository import NewsletterRepository
from .order_repository import OrderRepository
from .participant_repository import ParticipantRepository
from .scan_token_repository import ScanTokenRepository
from .settings_repository import SettingsRepository
from .error_log_repository import ErrorLogRepository

__all__ = [
    "BaseRepository",
    "EntranceScanRepository",
    "EventRepository",
    "JobRepository",
    "OrderRepository",
    "ParticipantRepository",
    "MembershipRepository",
    "MembershipRepositoryProtocol",
    "ParticipantRepositoryProtocol",
    "EventRepositoryProtocol",
    "PurchaseRepositoryProtocol",
    "MembershipSettingsRepositoryProtocol",
    "MessageRepository",
    "NewsletterRepository",
    "ScanTokenRepository",
    "SettingsRepository",
    "ErrorLogRepository",
]
