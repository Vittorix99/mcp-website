from __future__ import annotations

from typing import Any, Dict, List, Optional

from dto.preorder import CheckoutParticipantDTO, PreOrderCartItemDTO
from models import Event, EventOrder, EventPurchaseAccessType, PurchaseTypes


def checkout_participants_to_payload(participants: List[CheckoutParticipantDTO]) -> List[Dict[str, Any]]:
    return [participant.to_payload() for participant in participants]


def create_event_order_model(
    *,
    order_id: str,
    order_status: str,
    cart_item: PreOrderCartItemDTO,
    total: float,
    event: Event,
    participants: List[CheckoutParticipantDTO],
    membership_targets: List[CheckoutParticipantDTO],
    membership_fee: Optional[float],
    purchase_mode: EventPurchaseAccessType,
    membership_lookup: Dict[str, Dict[str, Any]],
    discount_code_id: Optional[str] = None,
    discount_code: Optional[str] = None,
    discount_amount: Optional[float] = None,
    original_price: Optional[float] = None,
) -> EventOrder:
    return EventOrder(
        order_id=order_id,
        order_status=order_status,
        purchase_type=PurchaseTypes.EVENT,
        cart=[cart_item.to_payload()],
        total=total,
        reference_id=cart_item.event_id,
        event_meta=dict(cart_item.event_meta or {}),
        event_id=cart_item.event_id,
        participants=checkout_participants_to_payload(participants),
        event_price=float(event.price or 0),
        event_fee=float(event.fee or 0),
        membership_targets=checkout_participants_to_payload(membership_targets),
        membership_fee=membership_fee,
        purchase_mode=purchase_mode,
        discount_code_id=discount_code_id,
        discount_code=discount_code,
        discount_amount=discount_amount,
        original_price=original_price,
        membership_lookup=membership_lookup,
    )
