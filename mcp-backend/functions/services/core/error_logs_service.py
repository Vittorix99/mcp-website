import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dto.error_log import ErrorLogDTO
from interfaces.repositories import ErrorLogRepositoryProtocol
from repositories.error_log_repository import ErrorLogRepository

logger = logging.getLogger("ErrorLogsService")


def _normalize_message(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        primary = value.get("error") or value.get("message")
        details = []

        invalid_emails = value.get("invalid_emails")
        if isinstance(invalid_emails, list) and invalid_emails:
            details.append("Invalid: " + ", ".join(str(item) for item in invalid_emails))

        non_existing = value.get("non_existing_subscribers")
        if isinstance(non_existing, list) and non_existing:
            details.append("Missing: " + ", ".join(str(item) for item in non_existing))

        if isinstance(primary, str) and (primary or details):
            return " | ".join([primary, *details] if primary else details)

    try:
        return json.dumps(value, ensure_ascii=True, default=str)
    except Exception:
        return str(value)


class ErrorLogsService:
    def __init__(self, repository: Optional[ErrorLogRepositoryProtocol] = None):
        self.repository = repository or ErrorLogRepository()

    def list_logs(self, limit: int = 100, service: Optional[str] = None, resolved: Optional[bool] = None):
        return [entry.to_payload() for entry in self.repository.list_dtos(limit=limit, service=service, resolved=resolved)]

    def get_log(self, error_log_id: str):
        dto = self.repository.get_dto(error_log_id)
        return dto.to_payload() if dto else None

    def create_log(self, payload: Dict[str, Any]):
        dto = ErrorLogDTO.from_payload(payload or {})
        dto.message = _normalize_message(dto.message)
        if not dto.service:
            raise ValueError("Missing service")
        if not dto.message:
            raise ValueError("Missing message")
        dto.created_at = dto.created_at or datetime.now(timezone.utc).isoformat()
        dto.severity = dto.severity or "error"
        dto.resolved = bool(dto.resolved) if dto.resolved is not None else False
        error_log_id = self.repository.create_from_dto(dto)
        created = self.get_log(error_log_id) or {}
        created["id"] = error_log_id
        return created

    def update_log(self, error_log_id: str, payload: Dict[str, Any]):
        current = self.get_log(error_log_id)
        if not current:
            return None
        updates = dict(payload or {})
        if "message" in updates:
            updates["message"] = _normalize_message(updates.get("message"))
        self.repository.update_from_payload(error_log_id, updates)
        updated = self.get_log(error_log_id) or {}
        updated["id"] = error_log_id
        return updated

    def delete_log(self, error_log_id: str) -> bool:
        if not self.repository.get_model(error_log_id):
            return False
        self.repository.delete(error_log_id)
        return True


def log_external_error(
    service: str,
    message: str,
    operation: Optional[str] = None,
    source: Optional[str] = None,
    status_code: Optional[int] = None,
    payload: Any = None,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "error",
) -> None:
    """Non-blocking external error logger used by routes/services/triggers."""
    try:
        ErrorLogsService().create_log(
            {
                "service": service,
                "message": message,
                "operation": operation,
                "source": source,
                "status_code": status_code,
                "payload": payload,
                "context": context,
                "severity": severity or "error",
                "resolved": False,
            }
        )
    except Exception as exc:
        logger.debug("Failed to persist external error log: %s", exc)
