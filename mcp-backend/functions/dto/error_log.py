from dataclasses import dataclass
from typing import Any, Dict, Optional

from models import ErrorLog


@dataclass
class ErrorLogDTO:
    id: Optional[str] = None
    service: Optional[str] = None
    operation: Optional[str] = None
    source: Optional[str] = None
    message: Optional[str] = None
    status_code: Optional[int] = None
    payload: Optional[Any] = None
    context: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    resolved: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_model(cls, model: ErrorLog) -> "ErrorLogDTO":
        return cls(
            id=model.id,
            service=model.service,
            operation=model.operation,
            source=model.source,
            message=model.message,
            status_code=model.status_code,
            payload=model.payload,
            context=model.context,
            severity=model.severity,
            resolved=model.resolved,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ErrorLogDTO":
        return cls(
            id=payload.get("id"),
            service=payload.get("service"),
            operation=payload.get("operation"),
            source=payload.get("source"),
            message=payload.get("message"),
            status_code=payload.get("status_code"),
            payload=payload.get("payload"),
            context=payload.get("context"),
            severity=payload.get("severity"),
            resolved=payload.get("resolved"),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
        )

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "id": self.id,
            "service": self.service,
            "operation": self.operation,
            "source": self.source,
            "message": self.message,
            "status_code": self.status_code,
            "payload": self.payload,
            "context": self.context,
            "severity": self.severity,
            "resolved": self.resolved,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return {k: v for k, v in payload.items() if v is not None}

    def to_model(self) -> ErrorLog:
        return ErrorLog(
            id=self.id,
            service=self.service or "",
            operation=self.operation,
            source=self.source,
            message=self.message or "",
            status_code=self.status_code,
            payload=self.payload,
            context=self.context,
            severity=self.severity or "error",
            resolved=bool(self.resolved) if self.resolved is not None else False,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
