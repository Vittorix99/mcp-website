"""
Raw HTTP wrappers for the Sender API (sender.net).
Base URL: https://api.sender.net/v2/

No business logic here — only HTTP calls and result parsing.
Mirrors the structure of routes/pass2u_routes.py.
"""
from dataclasses import dataclass
from typing import Any, Optional

import requests

from config.external_services import SENDER_BASE_URL
from services.core.error_logs_service import log_external_error


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
                source="routes.sender_routes._call",
                message=str(exc),
                status_code=0,
                context={"url": url},
            )
            raise
        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            error_message = cls._extract_error(payload) or str(payload)
            log_external_error(
                service="Sender",
                operation=f"{method.upper()} {endpoint}",
                source="routes.sender_routes._call",
                message=error_message or "Sender request failed",
                status_code=response.status_code,
                payload=payload,
                context={"url": url},
            )
        return SenderApiResult(
            status_code=response.status_code,
            payload=payload,
            error_message=error_message,
        )

    # ------------------------------------------------------------------ #
    # Subscribers
    # ------------------------------------------------------------------ #

    @classmethod
    def upsert_subscriber(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", "/subscribers", api_key, body=body, timeout=timeout)

    @classmethod
    def get_subscriber(cls, api_key: str, email: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/subscribers/{email}", api_key, timeout=timeout)

    @classmethod
    def update_subscriber(cls, api_key: str, email: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", f"/subscribers/{email}", api_key, body=body, timeout=timeout)

    @classmethod
    def delete_subscriber(cls, api_key: str, email: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", "/subscribers", api_key, body={"subscribers": [email]}, timeout=timeout)

    @classmethod
    def list_subscribers(cls, api_key: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", "/subscribers", api_key, params=params, timeout=timeout)

    @classmethod
    def add_to_group(cls, api_key: str, email: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", f"/subscribers/groups/{group_id}", api_key, body={"subscribers": [email]}, timeout=timeout)

    @classmethod
    def remove_from_group(cls, api_key: str, email: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", f"/subscribers/groups/{group_id}", api_key, body={"subscribers": [email]}, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Groups
    # ------------------------------------------------------------------ #

    @classmethod
    def list_groups(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", "/groups", api_key, timeout=timeout)

    @classmethod
    def get_group(cls, api_key: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/groups/{group_id}", api_key, timeout=timeout)

    @classmethod
    def create_group(cls, api_key: str, title: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", "/groups", api_key, body={"title": title}, timeout=timeout)

    @classmethod
    def rename_group(cls, api_key: str, group_id: str, title: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", f"/groups/{group_id}", api_key, body={"title": title}, timeout=timeout)

    @classmethod
    def delete_group(cls, api_key: str, group_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", f"/groups/{group_id}", api_key, timeout=timeout)

    @classmethod
    def list_group_subscribers(cls, api_key: str, group_id: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/groups/{group_id}/subscribers", api_key, params=params, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Fields
    # ------------------------------------------------------------------ #

    @classmethod
    def list_fields(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", "/fields", api_key, timeout=timeout)

    @classmethod
    def create_field(cls, api_key: str, title: str, field_type: str = "string", timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", "/fields", api_key, body={"title": title, "type": field_type}, timeout=timeout)

    @classmethod
    def rename_field(cls, api_key: str, field_id: str, title: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", f"/fields/{field_id}", api_key, body={"title": title}, timeout=timeout)

    @classmethod
    def delete_field(cls, api_key: str, field_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", f"/fields/{field_id}", api_key, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Segments
    # ------------------------------------------------------------------ #

    @classmethod
    def list_segments(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", "/segments", api_key, timeout=timeout)

    @classmethod
    def get_segment(cls, api_key: str, segment_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/segments/{segment_id}", api_key, timeout=timeout)

    @classmethod
    def list_segment_subscribers(cls, api_key: str, segment_id: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/segments/{segment_id}/subscribers", api_key, params=params, timeout=timeout)

    @classmethod
    def delete_segment(cls, api_key: str, segment_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", f"/segments/{segment_id}", api_key, timeout=timeout)

    @classmethod
    def get_subscriber_events(cls, api_key: str, identifier: str, actions: Optional[str] = None, timeout: int = 10) -> SenderApiResult:
        params = {}
        if actions:
            params["actions"] = actions
        return cls._call("GET", f"/subscribers/{identifier}/events", api_key, params=params, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Campaigns
    # ------------------------------------------------------------------ #

    @classmethod
    def list_campaigns(cls, api_key: str, params: Optional[dict] = None, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", "/campaigns", api_key, params=params, timeout=timeout)

    @classmethod
    def get_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}", api_key, timeout=timeout)

    @classmethod
    def create_campaign(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", "/campaigns", api_key, body=body, timeout=timeout)

    @classmethod
    def send_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", f"/campaigns/{campaign_id}/send", api_key, timeout=timeout)

    @classmethod
    def schedule_campaign(cls, api_key: str, campaign_id: str, schedule_time: str, timeout: int = 10) -> SenderApiResult:
        """schedule_time must be in 'Y-m-d H:i:s' format, e.g. '2025-06-01 18:00:00'"""
        return cls._call("POST", f"/campaigns/{campaign_id}/schedule", api_key, body={"schedule_time": schedule_time}, timeout=timeout)

    @classmethod
    def cancel_scheduled_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("DELETE", f"/campaigns/{campaign_id}/schedule", api_key, timeout=timeout)

    @classmethod
    def delete_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        url = f"{cls.BASE_URL.rstrip('/')}/campaigns"
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
                source="routes.sender_routes.delete_campaign",
                message=str(exc),
                status_code=0,
                context={"campaign_id": campaign_id},
            )
            raise
        payload = cls._parse_payload(response)
        error_message = cls._extract_error(payload) or str(payload) if response.status_code >= 400 else None
        if response.status_code >= 400:
            log_external_error(
                service="Sender",
                operation="DELETE /campaigns",
                source="routes.sender_routes.delete_campaign",
                message=error_message or "Sender delete campaign failed",
                status_code=response.status_code,
                payload=payload,
                context={"campaign_id": campaign_id},
            )
        return SenderApiResult(status_code=response.status_code, payload=payload, error_message=error_message)

    @classmethod
    def update_campaign(cls, api_key: str, campaign_id: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("PATCH", f"/campaigns/{campaign_id}", api_key, body=body, timeout=timeout)

    @classmethod
    def copy_campaign(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", f"/campaigns/{campaign_id}/copy", api_key, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Statistics  (GET /campaigns/{id}/{stat})
    # ------------------------------------------------------------------ #

    @classmethod
    def get_campaign_opens(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/opens", api_key, timeout=timeout)

    @classmethod
    def get_campaign_clicks(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/clicks", api_key, timeout=timeout)

    @classmethod
    def get_campaign_unsubscribes(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/unsubscribes", api_key, timeout=timeout)

    @classmethod
    def get_campaign_bounces_hard(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/hard_bounces", api_key, timeout=timeout)

    @classmethod
    def get_campaign_bounces_soft(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/soft_bounces", api_key, timeout=timeout)

    @classmethod
    def get_campaign_emails_sent(cls, api_key: str, campaign_id: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", f"/campaigns/{campaign_id}/emails-sent", api_key, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Transactional
    # ------------------------------------------------------------------ #

    @classmethod
    def send_transactional(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", "/message/send", api_key, body=body, timeout=timeout)

    @classmethod
    def list_transactional_campaigns(cls, api_key: str, timeout: int = 10) -> SenderApiResult:
        return cls._call("GET", "/transactional-campaigns", api_key, timeout=timeout)

    @classmethod
    def create_transactional_campaign(cls, api_key: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", "/transactional-campaigns", api_key, body=body, timeout=timeout)

    @classmethod
    def send_transactional_campaign(cls, api_key: str, campaign_id: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", f"/transactional-campaigns/{campaign_id}/send", api_key, body=body, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Workflows
    # ------------------------------------------------------------------ #

    @classmethod
    def start_workflow(cls, api_key: str, workflow_id: str, body: dict, timeout: int = 10) -> SenderApiResult:
        return cls._call("POST", f"/workflows/{workflow_id}/start", api_key, body=body, timeout=timeout)
