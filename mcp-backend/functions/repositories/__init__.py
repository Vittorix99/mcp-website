"""Repository helpers for Firestore persistence."""

from .admin_auth_repository import AdminAuthRepository
from .event_guide_repository import EventGuideRepository
from .event_location_repository import EventLocationRepository
from .admin_repository import AdminRepository
from .analytics_snapshot_repository import AnalyticsSnapshotRepository
from .base import BaseRepository
from .entrance_scan_repository import EntranceScanRepository
from .event_repository import EventRepository
from .job_repository import AnalyticsJobRepository, JobRepository, LocationJobRepository
from interfaces.repositories import (
    AdminAuthRepositoryProtocol,
    AdminRepositoryProtocol,
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

__all__ = [
    "AdminAuthRepository",
    "AdminRepository",
    "AdminAuthRepositoryProtocol",
    "AdminRepositoryProtocol",
    "AnalyticsSnapshotRepository",
    "BaseRepository",
    "EntranceScanRepository",
    "EventRepository",
    "EventGuideRepository",
    "EventLocationRepository",
    "JobRepository",
    "AnalyticsJobRepository",
    "LocationJobRepository",
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
]
