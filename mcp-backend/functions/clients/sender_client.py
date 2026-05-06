"""Client HTTP raw per Sender: niente business logic, solo chiamate e parsing."""
import logging
from dataclasses import dataclass
from typing import Any, Optional

import requests

from config.external_services import SENDER_BASE_URL
from services.core.error_logs_service import log_external_error
from utils.safe_logging import redact_sensitive

logger = logging.getLogger("sender_client")


class _Endpoints:
    # Subscribers
    SUBSCRIBERS = "/subscribers"
    SUBSCRIBER = "/subscribers/{email}"
    SUBSCRIBER_GROUPS = "/subscribers/groups/{group_id}"
    SUBSCRIBER_EVENTS = "/subscribers/{identifier}/events"
    # Groups
    GROUPS = "/groups"
    GROUP = "/groups/{group_id}"
    GROUP_SUBSCRIBERS = "/groups/{group_id}/subscribers"
    # Fields
    FIELDS = "/fields"
    FIELD = "/fields/{field_id}"
    # Segments
    SEGMENTS = "/segments"
    SEGMENT = "/segments/{segment_id}"
    SEGMENT_SUBSCRIBERS = "/segments/{segment_id}/subscribers"
    # Campaigns
    CAMPAIGNS = "/campaigns"
    CAMPAIGN = "/campaigns/{campaign_id}"
    CAMPAIGN_SEND = "/campaigns/{campaign_id}/send"
    CAMPAIGN_SCHEDULE = "/campaigns/{campaign_id}/schedule"
    CAMPAIGN_COPY = "/campaigns/{campaign_id}/copy"
    CAMPAIGN_OPENS = "/campaigns/{campaign_id}/opens"
    CAMPAIGN_CLICKS = "/campaigns/{campaign_id}/clicks"
    CAMPAIGN_UNSUBSCRIBES = "/campaigns/{campaign_id}/unsubscribes"
    CAMPAIGN_BOUNCES_HARD = "/campaigns/{campaign_id}/hard_bounces"
    CAMPAIGN_BOUNCES_SOFT = "/campaigns/{campaign_id}/soft_bounces"
    # Transactional
    TRANSACTIONAL_SEND = "/message/send"
    TRANSACTIONAL_CAMPAIGNS = "/transactional-campaigns"
    TRANSACTIONAL_CAMPAIGN_SEND = "/transactional-campaigns/{campaign_id}/send"
    # Workflows
    WORKFLOW_START = "/workflows/{workflow_id}/start"


@dataclass(frozen=True)
class SenderApiResult:
    status_code: int
    payload: Optional[Any] = None
    error_message: Optional[str] = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class SenderRoutes:
    BASE_URL = SENDER_BASE_URL

    @staticmethod
    def _parse_payload(response: requests.Response) -> Any:
        # Alcuni endpoint Sender rispondono senza body: il payload resta None.
        if not response.content:
            return None
        try:
            return response.json()
        except Exception:
            return response.text

    @staticmethod
    def _extract_error(payload: Any) -> Optional[str]:
        if isinstance(payload, dict):
            return payload.get("message") or payload.get("error")
        return None

    @classmethod
    def _headers(cls, api_key: str) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @classmethod
    def _call(
        cls,
        method: str,
        endpoint: str,
        api_key: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: int = 10,
    ) -> SenderApiResult:
        url = f"{cls.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            # Tutte le API Sender passano da qui per avere logging/error handling uniforme.
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=cls._headers(api_key),
                json=body,
                params=params,
                timeout=timeout,
            )
        except Exception as exc:
            log_external_error(
                service="Sender",
                operation=f"{method.upper()} {endpoint}",
                source="clients.sender_client._call",
                message=str(exc),
                status_code=0,
                context={"url": url},
            )
            raise

        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            # L'errore del provider viene normalizzato, non interpretato dal client.
            error_message = cls._extract_error(payload) or str(payload)
            log_external_error(
                service="Sender",
                operation=f"{method.upper()} {endpoint}",
                source="clients.sender_client._call",
                message=error_message,
                status_code=response.status_code,
                payload=payload,
                context={"url": url},
            )
        else:
            logger.info("%s %s -> %d", method.upper(), redact_sensitive(endpoint), response.status_code)

        return SenderApiResult(
            status_code=response.status_code,
            payload=payload,
            error_message=error_message,
        )

    # ── Subscribers ───────────────────────────────────────────────────────────

    @classmethod
    def upsert_subscriber(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.SUBSCRIBERS, api_key, body=body, timeout=timeout)

    @classmethod
    def get_subscriber(cls, api_key: str, email: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.SUBSCRIBER.format(email=email), api_key, timeout=timeout)

    @classmethod
    def update_subscriber(cls, api_key: str, email: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", _Endpoints.SUBSCRIBER.format(email=email), api_key, body=body, timeout=timeout)

    @classmethod
    def delete_subscriber(cls, api_key: str, email: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", _Endpoints.SUBSCRIBERS, api_key, body={"subscribers": [email]}, timeout=timeout)

    @classmethod
    def list_subscribers(cls, api_key: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.SUBSCRIBERS, api_key, params=params, timeout=timeout)

    @classmethod
    def add_to_group(cls, api_key: str, email: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.SUBSCRIBER_GROUPS.format(group_id=group_id), api_key, body={"subscribers": [email]}, timeout=timeout)

    @classmethod
    def remove_from_group(cls, api_key: str, email: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", _Endpoints.SUBSCRIBER_GROUPS.format(group_id=group_id), api_key, body={"subscribers": [email]}, timeout=timeout)

    @classmethod
    def get_subscriber_events(cls, api_key: str, identifier: str, actions: Optional[str] = None, timeout: int = 10) -> SenderApiResult:
        params = {"actions": actions} if actions else {}
        return cls._call("GET", _Endpoints.SUBSCRIBER_EVENTS.format(identifier=identifier), api_key, params=params, timeout=timeout)

    # ── Groups ────────────────────────────────────────────────────────────────

    @classmethod
    def list_groups(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.GROUPS, api_key, timeout=timeout)

    @classmethod
    def get_group(cls, api_key: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.GROUP.format(group_id=group_id), api_key, timeout=timeout)

    @classmethod
    def create_group(cls, api_key: str, title: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.GROUPS, api_key, body={"title": title}, timeout=timeout)

    @classmethod
    def rename_group(cls, api_key: str, group_id: str, title: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", _Endpoints.GROUP.format(group_id=group_id), api_key, body={"title": title}, timeout=timeout)

    @classmethod
    def delete_group(cls, api_key: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", _Endpoints.GROUP.format(group_id=group_id), api_key, timeout=timeout)

    @classmethod
    def list_group_subscribers(cls, api_key: str, group_id: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.GROUP_SUBSCRIBERS.format(group_id=group_id), api_key, params=params, timeout=timeout)

    # ── Fields ────────────────────────────────────────────────────────────────

    @classmethod
    def list_fields(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.FIELDS, api_key, timeout=timeout)

    @classmethod
    def create_field(cls, api_key: str, title: str, field_type: str = "string", timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.FIELDS, api_key, body={"title": title, "type": field_type}, timeout=timeout)

    @classmethod
    def rename_field(cls, api_key: str, field_id: str, title: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", _Endpoints.FIELD.format(field_id=field_id), api_key, body={"title": title}, timeout=timeout)

    @classmethod
    def delete_field(cls, api_key: str, field_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", _Endpoints.FIELD.format(field_id=field_id), api_key, timeout=timeout)

    # ── Segments ──────────────────────────────────────────────────────────────

    @classmethod
    def list_segments(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.SEGMENTS, api_key, timeout=timeout)

    @classmethod
    def get_segment(cls, api_key: str, segment_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.SEGMENT.format(segment_id=segment_id), api_key, timeout=timeout)

    @classmethod
    def list_segment_subscribers(cls, api_key: str, segment_id: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.SEGMENT_SUBSCRIBERS.format(segment_id=segment_id), api_key, params=params, timeout=timeout)

    @classmethod
    def delete_segment(cls, api_key: str, segment_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", _Endpoints.SEGMENT.format(segment_id=segment_id), api_key, timeout=timeout)

    # ── Campaigns ─────────────────────────────────────────────────────────────

    @classmethod
    def list_campaigns(cls, api_key: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGNS, api_key, params=params, timeout=timeout)

    @classmethod
    def get_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGN.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def create_campaign(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.CAMPAIGNS, api_key, body=body, timeout=timeout)

    @classmethod
    def send_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.CAMPAIGN_SEND.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def schedule_campaign(cls, api_key: str, campaign_id: str, schedule_time: str, timeout: int = 10) -> SenderApiResult:
        """schedule_time must be in 'Y-m-d H:i:s' format, e.g. '2025-06-01 18:00:00'"""
        return cls._call("POST", _Endpoints.CAMPAIGN_SCHEDULE.format(campaign_id=campaign_id), api_key, body={"schedule_time": schedule_time}, timeout=timeout)

    @classmethod
    def cancel_scheduled_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", _Endpoints.CAMPAIGN_SCHEDULE.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def delete_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        # Sender uses query param ids=[id] for DELETE /campaigns
        url = f"{cls.BASE_URL.rstrip('/')}{_Endpoints.CAMPAIGNS}"
        try:
            response = requests.request(
                method="DELETE",
                url=url,
                headers=cls._headers(api_key),
                params={"ids": f"[{campaign_id}]"},
                timeout=timeout,
            )
        except Exception as exc:
            log_external_error(
                service="Sender",
                operation="DELETE /campaigns",
                source="clients.sender_client.delete_campaign",
                message=str(exc),
                status_code=0,
                context={"campaign_id": campaign_id},
            )
            raise
        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            error_message = cls._extract_error(payload) or str(payload)
            log_external_error(
                service="Sender",
                operation="DELETE /campaigns",
                source="clients.sender_client.delete_campaign",
                message=error_message,
                status_code=response.status_code,
                payload=payload,
                context={"campaign_id": campaign_id},
            )
        else:
            logger.info("DELETE %s -> %d", _Endpoints.CAMPAIGNS, response.status_code)
        return SenderApiResult(status_code=response.status_code, payload=payload, error_message=error_message)

    @classmethod
    def update_campaign(cls, api_key: str, campaign_id: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", _Endpoints.CAMPAIGN.format(campaign_id=campaign_id), api_key, body=body, timeout=timeout)

    @classmethod
    def copy_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.CAMPAIGN_COPY.format(campaign_id=campaign_id), api_key, timeout=timeout)

    # ── Campaign statistics ───────────────────────────────────────────────────

    @classmethod
    def get_campaign_opens(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGN_OPENS.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def get_campaign_clicks(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGN_CLICKS.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def get_campaign_unsubscribes(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGN_UNSUBSCRIBES.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def get_campaign_bounces_hard(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGN_BOUNCES_HARD.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def get_campaign_bounces_soft(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.CAMPAIGN_BOUNCES_SOFT.format(campaign_id=campaign_id), api_key, timeout=timeout)

    @classmethod
    def get_campaign_emails_sent(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/emails-sent", api_key, timeout=timeout)

    # ── Transactional ─────────────────────────────────────────────────────────

    @classmethod
    def send_transactional(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.TRANSACTIONAL_SEND, api_key, body=body, timeout=timeout)

    @classmethod
    def list_transactional_campaigns(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", _Endpoints.TRANSACTIONAL_CAMPAIGNS, api_key, timeout=timeout)

    @classmethod
    def create_transactional_campaign(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.TRANSACTIONAL_CAMPAIGNS, api_key, body=body, timeout=timeout)

    @classmethod
    def send_transactional_campaign(cls, api_key: str, campaign_id: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.TRANSACTIONAL_CAMPAIGN_SEND.format(campaign_id=campaign_id), api_key, body=body, timeout=timeout)

    # ── Workflows ─────────────────────────────────────────────────────────────

    @classmethod
    def start_workflow(cls, api_key: str, workflow_id: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", _Endpoints.WORKFLOW_START.format(workflow_id=workflow_id), api_key, body=body, timeout=timeout)
