from dataclasses import dataclass
from typing import Any, Dict, Optional

from models import Job


@dataclass
class JobDTO:
    id: Optional[str] = None
    type: Optional[str] = None
    event_id: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    total: Optional[int] = None
    sent: Optional[int] = None
    failed: Optional[int] = None
    percent: Optional[int] = None
    created_at: Optional[Any] = None
    error: Optional[str] = None

    @classmethod
    def from_model(cls, job: Job) -> "JobDTO":
        return cls(
            id=job.id,
            type=job.type,
            event_id=job.event_id,
            status=job.status,
            address=job.address,
            link=job.link,
            message=job.message,
            total=job.total,
            sent=job.sent,
            failed=job.failed,
            percent=job.percent,
            created_at=job.created_at,
            error=job.error,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "event_id": self.event_id,
            "status": self.status,
            "address": self.address,
            "link": self.link,
            "message": self.message,
            "total": self.total,
            "sent": self.sent,
            "failed": self.failed,
            "percent": self.percent,
            "created_at": self.created_at,
            "error": self.error,
        }
        return {k: v for k, v in payload.items() if v is not None}

    def to_update_payload(self) -> Dict[str, Any]:
        payload = self.to_payload()
        payload.pop("id", None)
        return payload
