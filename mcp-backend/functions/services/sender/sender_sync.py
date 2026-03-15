"""
Sync functions that translate domain events into Sender subscriber operations.
Called from Firestore triggers and public API endpoints.

Each function accepts typed domain models (Membership, EventParticipant) or
a SenderSubscriberDTO — never raw Firestore dicts.

All functions log errors and never raise — they are fire-and-forget.

Group assignment rules:
  - Membership created          → "Memberships"
  - Participant (consent=True)  → "Newsletter" + "Participant-{event_title}"
  - Newsletter signup (public)  → "Newsletter"
"""
import logging
from typing import List, Optional

from config.external_services import (
    SENDER_GROUP_MEMBERS,
    SENDER_GROUP_TICKET_BUYERS,
)
from dto.sender_subscriber import SenderSubscriberDTO
from models.membership import Membership
from models.event_participant import EventParticipant
from services.sender.sender_service import SenderService

logger = logging.getLogger("SenderSync")


def _find_or_create_group(svc: SenderService, title: str) -> Optional[str]:
    """Return group ID for title (case-insensitive), creating it if not found."""
    payload = svc.list_groups()
    groups = payload.get("data", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
    for g in groups:
        if str(g.get("title", "")).strip().lower() == title.strip().lower():
            return str(g["id"])
    new_payload = svc.create_group(title)
    if new_payload:
        gid = (new_payload.get("data") or {}).get("id") or new_payload.get("id")
        if gid:
            return str(gid)
    return None


def _upsert(dto: SenderSubscriberDTO, group_ids: List[Optional[str]], context: str) -> None:
    """Internal helper — upserts a subscriber and assigns them to one or more groups."""
    if not dto.email:
        logger.warning("[SenderSync] %s: missing email, skipping", context)
        return
    valid_groups = [g for g in group_ids if g]
    if not valid_groups:
        logger.warning("[SenderSync] %s: no valid group_ids, skipping group assignment", context)
    try:
        SenderService().upsert_subscriber(**dto.to_upsert_kwargs(groups=valid_groups or None))
        logger.info("[SenderSync] %s: %s synced to Sender (source=%s)", context, dto.email, dto.source.value)
    except Exception as exc:
        logger.error("[SenderSync] %s: upsert failed for %s: %s", context, dto.email, exc)


def sync_membership_to_sender(membership_id: str, membership: Membership) -> None:
    """
    Called when a membership is created.
    Syncs to the "Memberships" group (find-or-create), falling back to
    SENDER_GROUP_MEMBERS env var if the dynamic lookup fails.
    """
    dto = SenderSubscriberDTO.from_membership(membership_id, membership)
    try:
        svc = SenderService()
        group_id = _find_or_create_group(svc, "Memberships")
        _upsert(dto, [group_id], "sync_membership_to_sender")
    except Exception as exc:
        logger.error("[SenderSync] sync_membership_to_sender: group find/create failed: %s", exc)
        _upsert(dto, [SENDER_GROUP_MEMBERS], "sync_membership_to_sender")


def sync_participant_to_sender(
    participant_id: str,
    participant: EventParticipant,
    event_id: str,
    event_title: Optional[str] = None,
) -> None:
    """
    Called when a participant is created with newsletter_consent = True.
    Always syncs to "Newsletter" group.
    Also syncs to "Participant-{event_title}" if event_title is provided,
    falling back to SENDER_GROUP_TICKET_BUYERS env var.
    """
    if not participant.newsletter_consent:
        logger.debug("[SenderSync] sync_participant_to_sender: no consent for %s, skipping", participant.email)
        return
    dto = SenderSubscriberDTO.from_participant(participant_id, participant, event_id)

    try:
        svc = SenderService()
        newsletter_group_id = _find_or_create_group(svc, "Newsletter")
        if event_title:
            per_event_group_id = _find_or_create_group(svc, f"Participant-{event_title}")
            _upsert(dto, [newsletter_group_id, per_event_group_id], "sync_participant_to_sender")
        else:
            logger.warning("[SenderSync] sync_participant_to_sender: no event_title for %s, using fallback group", participant.email)
            _upsert(dto, [newsletter_group_id, SENDER_GROUP_TICKET_BUYERS], "sync_participant_to_sender")
    except Exception as exc:
        logger.error("[SenderSync] sync_participant_to_sender: group find/create failed: %s", exc)
        _upsert(dto, [SENDER_GROUP_TICKET_BUYERS], "sync_participant_to_sender")


def sync_newsletter_signup_to_sender(email: str, name: Optional[str] = None) -> None:
    """
    Called when a public newsletter signup is submitted.
    Syncs to the "Newsletter" group (find-or-create).
    """
    dto = SenderSubscriberDTO.from_newsletter_signup(email, name)
    try:
        svc = SenderService()
        group_id = _find_or_create_group(svc, "Newsletter")
        _upsert(dto, [group_id], "sync_newsletter_signup_to_sender")
    except Exception as exc:
        logger.error("[SenderSync] sync_newsletter_signup_to_sender: group find/create failed: %s", exc)
        _upsert(dto, [], "sync_newsletter_signup_to_sender")


def unsubscribe_from_sender(email: str) -> None:
    """
    Soft unsubscribe: sets subscriber status to UNSUBSCRIBED.
    Preserves history, campaign stats and bounce data.
    This is the correct action for a normal opt-out / unsubscribe request.
    """
    email = (email or "").strip().lower()
    if not email:
        return
    try:
        SenderService().update_subscriber(email, {"subscriber_status": "UNSUBSCRIBED"})
        logger.info("[SenderSync] unsubscribe_from_sender: %s marked UNSUBSCRIBED", email)
    except Exception as exc:
        logger.error("[SenderSync] unsubscribe_from_sender(%s) failed: %s", email, exc)


def delete_subscriber_from_sender(email: str) -> None:
    """
    Hard delete: removes the subscriber entirely from Sender.
    Use ONLY for GDPR right-to-erasure requests — this destroys all history.
    For normal opt-outs, use unsubscribe_from_sender() instead.
    """
    email = (email or "").strip().lower()
    if not email:
        return
    try:
        SenderService().delete_subscriber(email)
        logger.info("[SenderSync] delete_subscriber_from_sender: %s deleted from Sender", email)
    except Exception as exc:
        logger.error("[SenderSync] delete_subscriber_from_sender(%s) failed: %s", email, exc)
