from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_data(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        if isinstance(payload.get("id"), (int, str)):
            return payload
    return {}


def _extract_list(payload: Any) -> List[Any]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return data
    return []


@dataclass
class MailerLiteGroupDTO:
    id: Optional[int] = None
    name: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    @classmethod
    def from_payload(cls, payload: Any) -> "MailerLiteGroupDTO":
        data = payload if isinstance(payload, dict) else {}
        return cls(
            id=_parse_int(data.get("id")),
            name=data.get("name"),
            raw=data if isinstance(data, dict) else None,
        )


@dataclass
class MailerLiteSubscriberDTO:
    id: Optional[int] = None
    email: Optional[str] = None
    status: Optional[str] = None
    fields: Dict[str, Any] = field(default_factory=dict)
    groups: List[MailerLiteGroupDTO] = field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None

    @property
    def id_str(self) -> Optional[str]:
        return str(self.id) if self.id is not None else None

    @classmethod
    def from_response(cls, payload: Any) -> Optional["MailerLiteSubscriberDTO"]:
        data = _extract_data(payload)
        if not data:
            return None
        raw_groups = data.get("groups") if isinstance(data, dict) else None
        groups = []
        if isinstance(raw_groups, list):
            groups = [MailerLiteGroupDTO.from_payload(item) for item in raw_groups]
        return cls(
            id=_parse_int(data.get("id")),
            email=data.get("email"),
            status=data.get("status"),
            fields=data.get("fields") if isinstance(data.get("fields"), dict) else {},
            groups=groups,
            raw=data,
        )


def parse_group_list(payload: Any) -> List[MailerLiteGroupDTO]:
    return [MailerLiteGroupDTO.from_payload(item) for item in _extract_list(payload) if isinstance(item, dict)]
