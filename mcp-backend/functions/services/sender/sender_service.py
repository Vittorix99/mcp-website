"""
Sender marketing service layer (sender.net).
Business logic that orchestrates calls to SenderRoutes.
Mirrors the purpose of services/mailer_lite/subscribers_client.py.

Never raises externally — logs errors and returns None/False on failure.
"""
import logging
from typing import Any, Dict, List, Optional

from config.external_services import SENDER_API_KEY
from routes.sender_routes import SenderRoutes, SenderApiResult
from services.core.error_logs_service import log_external_error

logger = logging.getLogger("SenderService")


def _format_sender_error(payload: Any, status_code: int) -> str:
    """Convert a Sender API error payload (may be a list of dicts) to a readable string."""
    if isinstance(payload, dict):
        errors = payload.get("error") or payload.get("errors") or payload.get("message")
        if isinstance(errors, list):
            parts = []
            for e in errors:
                if isinstance(e, dict):
                    title = e.get("title", "")
                    details = e.get("details", "")
                    parts.append(f"{title}: {details}" if title else details)
                else:
                    parts.append(str(e))
            return " | ".join(parts) if parts else f"HTTP {status_code}"
        if isinstance(errors, str):
            return errors
    return f"HTTP {status_code}"


class SenderService:
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or SENDER_API_KEY

    def _key(self) -> str:
        if not self._api_key:
            raise RuntimeError("SENDER_API_KEY non configurata")
        return self._api_key

    @staticmethod
    def _normalize_pagination(params: Optional[Dict]) -> Dict:
        """Translate frontend pagination params to Sender API params.
        Sender uses 'limit' (not 'per_page') and 'page'.
        """
        p = dict(params or {})
        if "per_page" in p:
            p["limit"] = p.pop("per_page")
        return p

    def _ok(self, result: SenderApiResult, context: str) -> bool:
        if not result.ok:
            logger.error("[Sender] %s failed (HTTP %s): %s", context, result.status_code, result.error_message or result.payload)
            log_external_error(
                service="Sender",
                operation=context,
                source="services.sender.sender_service._ok",
                message=result.error_message or "Sender request failed",
                status_code=result.status_code,
                payload=result.payload,
            )
            return False
        return True

    # ------------------------------------------------------------------ #
    # Subscribers
    # ------------------------------------------------------------------ #

    def upsert_subscriber(
        self,
        email: str,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        phone: Optional[str] = None,
        groups: Optional[List[str]] = None,
        fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict]:
        """Create or update a subscriber. Returns subscriber payload or None."""
        try:
            body: Dict[str, Any] = {"email": email}
            if firstname:
                body["firstname"] = firstname
            if lastname:
                body["lastname"] = lastname
            if phone:
                body["phone"] = phone
            if groups:
                body["groups"] = groups
            if fields:
                body["fields"] = fields
            result = SenderRoutes.upsert_subscriber(self._key(), body)
            if self._ok(result, f"upsert_subscriber({email})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] upsert_subscriber(%s) exception: %s", email, exc)
            return None

    def get_subscriber(self, email: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_subscriber(self._key(), email)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_subscriber(%s) exception: %s", email, exc)
            return None

    def update_subscriber(self, email: str, data: Dict) -> Optional[Dict]:
        try:
            result = SenderRoutes.update_subscriber(self._key(), email, data)
            if self._ok(result, f"update_subscriber({email})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] update_subscriber(%s) exception: %s", email, exc)
            return None

    def delete_subscriber(self, email: str) -> bool:
        try:
            result = SenderRoutes.delete_subscriber(self._key(), email)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] delete_subscriber(%s) exception: %s", email, exc)
            return False

    def add_to_group(self, email: str, group_id: str) -> bool:
        try:
            result = SenderRoutes.add_to_group(self._key(), email, group_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] add_to_group(%s, %s) exception: %s", email, group_id, exc)
            return False

    def remove_from_group(self, email: str, group_id: str) -> bool:
        try:
            result = SenderRoutes.remove_from_group(self._key(), email, group_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] remove_from_group(%s, %s) exception: %s", email, group_id, exc)
            return False

    def list_subscribers(self, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            normalized = self._normalize_pagination(params)
            result = SenderRoutes.list_subscribers(self._key(), params=normalized)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_subscribers exception: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Groups
    # ------------------------------------------------------------------ #

    def list_groups(self) -> Optional[Dict]:
        try:
            result = SenderRoutes.list_groups(self._key())
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_groups exception: %s", exc)
            return None

    def get_group(self, group_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_group(self._key(), group_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_group(%s) exception: %s", group_id, exc)
            return None

    def create_group(self, title: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.create_group(self._key(), title)
            if self._ok(result, f"create_group({title})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] create_group(%s) exception: %s", title, exc)
            return None

    def rename_group(self, group_id: str, title: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.rename_group(self._key(), group_id, title)
            if self._ok(result, f"rename_group({group_id})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] rename_group(%s) exception: %s", group_id, exc)
            return None

    def delete_group(self, group_id: str) -> bool:
        try:
            result = SenderRoutes.delete_group(self._key(), group_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] delete_group(%s) exception: %s", group_id, exc)
            return False

    def list_group_subscribers(self, group_id: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            normalized = self._normalize_pagination(params)
            result = SenderRoutes.list_group_subscribers(self._key(), group_id, params=normalized)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_group_subscribers(%s) exception: %s", group_id, exc)
            return None

    # ------------------------------------------------------------------ #
    # Fields
    # ------------------------------------------------------------------ #

    def list_fields(self) -> Optional[Dict]:
        try:
            result = SenderRoutes.list_fields(self._key())
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_fields exception: %s", exc)
            return None

    def create_field(self, title: str, field_type: str = "string") -> Optional[Dict]:
        try:
            result = SenderRoutes.create_field(self._key(), title, field_type)
            if self._ok(result, f"create_field({title})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] create_field(%s) exception: %s", title, exc)
            return None

    def rename_field(self, field_id: str, title: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.rename_field(self._key(), field_id, title)
            if self._ok(result, f"rename_field({field_id})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] rename_field(%s) exception: %s", field_id, exc)
            return None

    def delete_field(self, field_id: str) -> bool:
        try:
            result = SenderRoutes.delete_field(self._key(), field_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] delete_field(%s) exception: %s", field_id, exc)
            return False

    # ------------------------------------------------------------------ #
    # Segments
    # ------------------------------------------------------------------ #

    def list_segments(self) -> Optional[Dict]:
        try:
            result = SenderRoutes.list_segments(self._key())
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_segments exception: %s", exc)
            return None

    def get_segment(self, segment_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_segment(self._key(), segment_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_segment(%s) exception: %s", segment_id, exc)
            return None

    def list_segment_subscribers(self, segment_id: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            result = SenderRoutes.list_segment_subscribers(self._key(), segment_id, params=params)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_segment_subscribers(%s) exception: %s", segment_id, exc)
            return None

    def delete_segment(self, segment_id: str) -> bool:
        try:
            result = SenderRoutes.delete_segment(self._key(), segment_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] delete_segment(%s) exception: %s", segment_id, exc)
            return False

    def get_subscriber_events(self, identifier: str, actions: Optional[str] = None) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_subscriber_events(self._key(), identifier, actions=actions)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_subscriber_events(%s) exception: %s", identifier, exc)
            return None

    # ------------------------------------------------------------------ #
    # Campaigns
    # ------------------------------------------------------------------ #

    def list_campaigns(self, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            result = SenderRoutes.list_campaigns(self._key(), params=params)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_campaigns exception: %s", exc)
            return None

    def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_campaign(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_campaign(%s) exception: %s", campaign_id, exc)
            return None

    def create_campaign(
        self,
        title: str,
        subject: str,
        from_name: str,
        from_email: str,
        content_html: str,
        reply_to: Optional[str] = None,
        groups: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        try:
            body: Dict[str, Any] = {
                "title": title,
                "subject": subject,
                "from": from_name,          # display name string only
                "reply_to": reply_to or from_email,
                "content_type": "html",
                "content": content_html,    # HTML string directly, not nested object
            }
            if groups:
                body["groups"] = groups
            result = SenderRoutes.create_campaign(self._key(), body)
            if self._ok(result, f"create_campaign({title})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] create_campaign exception: %s", exc)
            return None

    def update_campaign(
        self,
        campaign_id: str,
        title: Optional[str] = None,
        subject: Optional[str] = None,
        from_name: Optional[str] = None,
        from_email: Optional[str] = None,
        content_html: Optional[str] = None,
        groups: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        try:
            body: Dict[str, Any] = {}
            if title is not None:
                body["title"] = title
            if subject is not None:
                body["subject"] = subject
            if from_name is not None:
                body["from"] = from_name
            if content_html is not None:
                body["content"] = content_html
                body["content_type"] = "html"
            if groups is not None:
                body["groups"] = groups
            result = SenderRoutes.update_campaign(self._key(), campaign_id, body)
            if self._ok(result, f"update_campaign({campaign_id})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] update_campaign(%s) exception: %s", campaign_id, exc)
            return None

    def send_campaign(self, campaign_id: str) -> tuple:
        """Returns (ok: bool, error: str | None)."""
        try:
            result = SenderRoutes.send_campaign(self._key(), campaign_id)
            if result.ok:
                return True, None
            error = _format_sender_error(result.payload, result.status_code)
            logger.error("[Sender] send_campaign(%s) failed: %s", campaign_id, error)
            return False, error
        except Exception as exc:
            logger.error("[Sender] send_campaign(%s) exception: %s", campaign_id, exc)
            return False, str(exc)

    def schedule_campaign(self, campaign_id: str, scheduled_at_iso: str) -> tuple:
        """Returns (ok: bool, error: str | None)."""
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(scheduled_at_iso.replace("Z", "+00:00"))
            schedule_time = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            result = SenderRoutes.schedule_campaign(self._key(), campaign_id, schedule_time)
            if result.ok:
                return True, None
            error = _format_sender_error(result.payload, result.status_code)
            logger.error("[Sender] schedule_campaign(%s) failed: %s", campaign_id, error)
            return False, error
        except Exception as exc:
            logger.error("[Sender] schedule_campaign(%s) exception: %s", campaign_id, exc)
            return False, str(exc)

    def cancel_scheduled_campaign(self, campaign_id: str) -> bool:
        try:
            result = SenderRoutes.cancel_scheduled_campaign(self._key(), campaign_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] cancel_scheduled_campaign(%s) exception: %s", campaign_id, exc)
            return False

    def delete_campaign(self, campaign_id: str) -> bool:
        try:
            result = SenderRoutes.delete_campaign(self._key(), campaign_id)
            return result.ok
        except Exception as exc:
            logger.error("[Sender] delete_campaign(%s) exception: %s", campaign_id, exc)
            return False

    def copy_campaign(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.copy_campaign(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] copy_campaign(%s) exception: %s", campaign_id, exc)
            return None

    # ------------------------------------------------------------------ #
    # Statistics
    # ------------------------------------------------------------------ #

    def get_campaign_opens(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_campaign_opens(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_campaign_opens exception: %s", exc)
            return None

    def get_campaign_clicks(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_campaign_clicks(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_campaign_clicks exception: %s", exc)
            return None

    def get_campaign_unsubscribes(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_campaign_unsubscribes(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_campaign_unsubscribes exception: %s", exc)
            return None

    def get_campaign_bounces_hard(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_campaign_bounces_hard(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_campaign_bounces_hard exception: %s", exc)
            return None

    def get_campaign_bounces_soft(self, campaign_id: str) -> Optional[Dict]:
        try:
            result = SenderRoutes.get_campaign_bounces_soft(self._key(), campaign_id)
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] get_campaign_bounces_soft exception: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Transactional
    # ------------------------------------------------------------------ #

    def send_transactional(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html: str,
        variables: Optional[Dict] = None,
        attachments: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict]:
        """Send a one-off transactional email (no template)."""
        try:
            body: Dict[str, Any] = {
                "to": [{"email": to_email, "name": to_name}],
                "subject": subject,
                "html": html,
            }
            if variables:
                body["variables"] = variables
            if attachments:
                body["attachments"] = [
                    {"filename": name, "url": url}
                    for name, url in attachments.items()
                ]
            result = SenderRoutes.send_transactional(self._key(), body)
            if self._ok(result, f"send_transactional({to_email})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] send_transactional(%s) exception: %s", to_email, exc)
            return None

    def list_transactional_campaigns(self) -> Optional[Dict]:
        try:
            result = SenderRoutes.list_transactional_campaigns(self._key())
            return result.payload if result.ok else None
        except Exception as exc:
            logger.error("[Sender] list_transactional_campaigns exception: %s", exc)
            return None

    def create_transactional_campaign(
        self,
        title: str,
        subject: str,
        from_name: str,
        from_email: str,
        content_html: str,
    ) -> Optional[Dict]:
        try:
            body = {
                "title": title,
                "subject": subject,
                "from": {"name": from_name, "email": from_email},
                "content": {"html": content_html},
            }
            result = SenderRoutes.create_transactional_campaign(self._key(), body)
            if self._ok(result, f"create_transactional_campaign({title})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] create_transactional_campaign exception: %s", exc)
            return None

    def send_transactional_campaign(
        self,
        campaign_id: str,
        to_email: str,
        to_name: str,
        variables: Optional[Dict] = None,
    ) -> Optional[Dict]:
        try:
            body: Dict[str, Any] = {"to": [{"email": to_email, "name": to_name}]}
            if variables:
                body["variables"] = variables
            result = SenderRoutes.send_transactional_campaign(self._key(), campaign_id, body)
            if self._ok(result, f"send_transactional_campaign({campaign_id}, {to_email})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] send_transactional_campaign exception: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Workflows
    # ------------------------------------------------------------------ #

    def start_workflow(
        self,
        workflow_id: str,
        email: str,
        variables: Optional[Dict] = None,
    ) -> Optional[Dict]:
        try:
            body: Dict[str, Any] = {"email": email}
            if variables:
                body["variables"] = variables
            result = SenderRoutes.start_workflow(self._key(), workflow_id, body)
            if self._ok(result, f"start_workflow({workflow_id}, {email})"):
                return result.payload
            return None
        except Exception as exc:
            logger.error("[Sender] start_workflow exception: %s", exc)
            return None
