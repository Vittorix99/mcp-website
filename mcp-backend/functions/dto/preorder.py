from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _build_participants(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [dict(p) if isinstance(p, dict) else {} for p in value]
    return []


@dataclass
class PreOrderCartItemDTO:
    eventId: str
    participants: List[Dict[str, Any]] = field(default_factory=list)
    membershipFee: Optional[float] = None
    eventMeta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PreOrderCartItemDTO":
        return cls(
            eventId=payload.get("eventId", ""),
            participants=_build_participants(payload.get("participants")),
            membershipFee=payload.get("membershipFee"),
            eventMeta=payload.get("eventMeta") or {},
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "eventId": self.eventId,
            "participants": self.participants,
            "membershipFee": self.membershipFee,
            "eventMeta": self.eventMeta,
        }
        return {k: v for k, v in payload.items() if v not in ({}, None) or k == "participants"}


@dataclass
class PreOrderDTO:
    cart: List[PreOrderCartItemDTO] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PreOrderDTO":
        raw_cart = payload.get("cart") or []
        cart_items: List[PreOrderCartItemDTO] = []
        for entry in raw_cart:
            if isinstance(entry, dict):
                cart_items.append(PreOrderCartItemDTO.from_payload(entry))
        return cls(cart=cart_items)

    def to_payload(self) -> Dict[str, Any]:
        return {"cart": [item.to_payload() for item in self.cart]}


@dataclass
class OrderCaptureDTO:
    order_id: str

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "OrderCaptureDTO":
        return cls(order_id=payload.get("order_id", ""))

    def to_payload(self) -> Dict[str, Any]:
        return {"order_id": self.order_id}
