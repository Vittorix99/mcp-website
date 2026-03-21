from dataclasses import dataclass
from typing import Any, Dict, Optional

from models import Setting


@dataclass
class SettingDTO:
    key: Optional[str] = None
    value: Any = None

    @classmethod
    def from_model(cls, setting: Setting) -> "SettingDTO":
        return cls(key=setting.key, value=setting.value)

    def to_payload(self) -> Dict[str, Any]:
        payload = {"key": self.key, "value": self.value}
        return {k: v for k, v in payload.items() if v is not None}

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "SettingDTO":
        return cls(key=payload.get("key"), value=payload.get("value"))
