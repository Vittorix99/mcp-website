import logging
from dataclasses import dataclass
from typing import Any, Optional

import requests

from config.external_services import PASS2U_BASE_URL
from services.core.error_logs_service import log_external_error
from utils.safe_logging import redact_sensitive, safe_id

logger = logging.getLogger("pass2u_client")


class _Endpoints:
    CREATE_PASS = "/models/{model_id}/passes"
    INVALIDATE_PASS = "/passes/{pass_id}"


@dataclass(frozen=True)
class Pass2UApiResult:
    status_code: int
    payload: Optional[Any] = None
    error_message: Optional[str] = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class Pass2URoutes:
    """Client HTTP Pass2U: nessuna business logic, solo request/response del provider."""

    @staticmethod
    def _url(path: str) -> str:
        return f"{PASS2U_BASE_URL.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _parse_payload(response: requests.Response) -> Any:
        # Pass2U non garantisce sempre JSON: conserviamo il body testuale come fallback.
        try:
            return response.json()
        except Exception:
            return response.text

    @classmethod
    def _extract_error(cls, payload: Any) -> Optional[str]:
        if isinstance(payload, dict):
            return str(redact_sensitive(payload.get("errorMessage") or payload.get("message")))
        return str(redact_sensitive(payload)) if payload else None

    @classmethod
    def create_pass(
        cls,
        model_id: str,
        api_key: str,
        body: dict,
        timeout: int = 10,
    ) -> Pass2UApiResult:
        url = cls._url(_Endpoints.CREATE_PASS.format(model_id=model_id))
        try:
            # Boundary esterno: il service prepara il body, il client si limita a spedirlo.
            response = requests.post(
                url,
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
                source="clients.pass2u_client.create_pass",
                message=str(exc),
                status_code=0,
                context={"model_id": model_id},
            )
            raise

        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            # Errori HTTP del provider non diventano eccezioni: tornano come risultato tipizzato.
            error_message = cls._extract_error(payload) or str(payload)
            log_external_error(
                service="Pass2U",
                operation="create_pass",
                source="clients.pass2u_client.create_pass",
                message=error_message,
                status_code=response.status_code,
                payload=payload,
                context={"model_id": model_id},
            )
        else:
            logger.info("create_pass: model=%s status=%d", safe_id(model_id), response.status_code)

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
        url = cls._url(_Endpoints.INVALIDATE_PASS.format(pass_id=pass_id))
        try:
            # L'invalidazione e' best-effort nei service: qui registriamo comunque l'esito Pass2U.
            response = requests.delete(
                url,
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
                source="clients.pass2u_client.invalidate_pass",
                message=str(exc),
                status_code=0,
                context={"pass_id": pass_id},
            )
            raise

        payload = cls._parse_payload(response)
        error_message = None
        if response.status_code >= 400:
            error_message = cls._extract_error(payload) or str(payload)
            log_external_error(
                service="Pass2U",
                operation="invalidate_pass",
                source="clients.pass2u_client.invalidate_pass",
                message=error_message,
                status_code=response.status_code,
                payload=payload,
                context={"pass_id": pass_id},
            )
        else:
            logger.info("invalidate_pass: pass_id=%s status=%d", safe_id(pass_id), response.status_code)

        return Pass2UApiResult(
            status_code=response.status_code,
            payload=payload,
            error_message=error_message,
        )
