from dataclasses import dataclass
from typing import Any, Optional

import requests

from config.external_services import PASS2U_BASE_URL
from services.core.error_logs_service import log_external_error


@dataclass(frozen=True)
class Pass2UApiResult:
    status_code: int
    payload: Optional[Any] = None
    error_message: Optional[str] = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class Pass2URoutes:
    @staticmethod
    def _parse_payload(response: requests.Response) -> Any:
        try:
            return response.json()
        except Exception:
            return response.text

    @classmethod
    def create_pass(
        cls,
        model_id: str,
        api_key: str,
        body: dict,
        timeout: int = 10,
    ) -> Pass2UApiResult:
        try:
            response = requests.post(
                f"{PASS2U_BASE_URL}/models/{model_id}/passes",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=body,
                timeout=timeout,
            )
        except Exception as exc:
            log_external_error(
                service="Pass2U",
                operation="create_pass",
                source="routes.pass2u_routes.create_pass",
                message=str(exc),
                status_code=0,
                context={"model_id": model_id},
            )
            raise
        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            if isinstance(payload, dict):
                error_message = payload.get("errorMessage") or payload.get("message")
            if not error_message:
                error_message = str(payload)
            log_external_error(
                service="Pass2U",
                operation="create_pass",
                source="routes.pass2u_routes.create_pass",
                message=error_message or "Pass2U create pass failed",
                status_code=response.status_code,
                payload=payload,
                context={"model_id": model_id},
            )

        return Pass2UApiResult(
            status_code=response.status_code,
            payload=payload,
            error_message=error_message,
        )

    @classmethod
    def invalidate_pass(
        cls,
        pass_id: str,
        api_key: str,
        timeout: int = 10,
    ) -> Pass2UApiResult:
        try:
            response = requests.delete(
                f"{PASS2U_BASE_URL}/passes/{pass_id}",
                headers={
                    "x-api-key": api_key,
                    "Accept": "application/json",
                },
                timeout=timeout,
            )
        except Exception as exc:
            log_external_error(
                service="Pass2U",
                operation="invalidate_pass",
                source="routes.pass2u_routes.invalidate_pass",
                message=str(exc),
                status_code=0,
                context={"pass_id": pass_id},
            )
            raise
        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            if isinstance(payload, dict):
                error_message = payload.get("errorMessage") or payload.get("message")
            if not error_message:
                error_message = str(payload)
            log_external_error(
                service="Pass2U",
                operation="invalidate_pass",
                source="routes.pass2u_routes.invalidate_pass",
                message=error_message or "Pass2U invalidate pass failed",
                status_code=response.status_code,
                payload=payload,
                context={"pass_id": pass_id},
            )

        return Pass2UApiResult(
            status_code=response.status_code,
            payload=payload,
            error_message=error_message,
        )
