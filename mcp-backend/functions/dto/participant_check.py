from dataclasses import dataclass, field
from typing import Any, Dict, List


def _normalize_participants(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized = []
    for entry in value:
        if isinstance(entry, dict):
            normalized.append(entry)
    return normalized


@dataclass
class ParticipantsCheckDTO:
    event_id: str
    participants: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ParticipantsCheckDTO":
        return cls(
            event_id=payload.get("eventId") or payload.get("event_id") or "",
            participants=_normalize_participants(payload.get("participants")),
        )

    def to_payload(self) -> Dict[str, Any]:
        return {"eventId": self.event_id, "participants": self.participants}
