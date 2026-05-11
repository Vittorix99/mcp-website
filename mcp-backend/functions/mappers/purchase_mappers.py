from __future__ import annotations

from dto.preorder import EventOrderCreateResponseDTO, OrderCaptureResponseDTO
from dto.purchase import CreatePurchaseRequestDTO, PurchaseDTO
from models import EventPurchase, EventPurchaseAccessType, PayPalOrderCreateResponse, Purchase, PurchaseTypes


def create_purchase_dto_to_model(dto: CreatePurchaseRequestDTO) -> Purchase:
    purchase_type = PurchaseTypes(dto.purchase_type)
    common_kwargs = {
        "payer_name": dto.payer_name,
        "payer_surname": dto.payer_surname,
        "slug": dto.slug,
        "payer_email": dto.payer_email,
        "amount_total": dto.amount_total,
        "currency": dto.currency,
        "paypal_fee": dto.paypal_fee,
        "net_amount": dto.net_amount,
        "transaction_id": dto.transaction_id,
        "order_id": dto.order_id,
        "status": dto.status,
        "timestamp": dto.timestamp,
        "ref_id": dto.ref_id,
        "payment_method": dto.payment_method,
        "capture_status": dto.capture_status,
    }

    if purchase_type == PurchaseTypes.EVENT:
        return EventPurchase(
            **common_kwargs,
            event_id=dto.event_id,
            event_purchase_type=EventPurchaseAccessType(
                dto.event_purchase_type or EventPurchaseAccessType.PUBLIC
            ),
            participants_count=dto.participants_count or 0,
            membership_ids=list(dto.membership_ids),
            discount_code_id=dto.discount_code_id,
            discount_code=dto.discount_code,
            discount_amount=dto.discount_amount,
        )

    return Purchase(
        **common_kwargs,
        purchase_type=purchase_type,
    )


def purchase_to_response(purchase: Purchase) -> PurchaseDTO:
    return PurchaseDTO(
        id=purchase.id,
        payer_name=purchase.payer_name,
        payer_surname=purchase.payer_surname,
        slug=purchase.slug,
        payer_email=purchase.payer_email,
        amount_total=purchase.amount_total,
        currency=purchase.currency,
        paypal_fee=purchase.paypal_fee,
        net_amount=purchase.net_amount,
        transaction_id=purchase.transaction_id,
        order_id=purchase.order_id,
        status=purchase.status,
        timestamp=purchase.timestamp,
        purchase_type=purchase.purchase_type,
        ref_id=purchase.ref_id,
        payment_method=purchase.payment_method,
        capture_status=purchase.capture_status,
        event_id=getattr(purchase, "event_id", None),
        event_purchase_type=getattr(purchase, "event_purchase_type", None),
        participants_count=getattr(purchase, "participants_count", None),
        membership_ids=list(getattr(purchase, "membership_ids", []) or []),
        discount_code_id=getattr(purchase, "discount_code_id", None),
        discount_code=getattr(purchase, "discount_code", None),
        discount_amount=getattr(purchase, "discount_amount", None),
    )


def paypal_order_create_to_response(order: PayPalOrderCreateResponse) -> EventOrderCreateResponseDTO:
    return EventOrderCreateResponseDTO(
        id=order.order_id,
        status=order.status,
        links=list(order.payload.get("links") or []),
    )


def order_capture_to_response(
    *,
    purchase_id: str,
    payment_method: str | None,
) -> OrderCaptureResponseDTO:
    return OrderCaptureResponseDTO(
        message="Order captured and processed successfully",
        purchase_id=purchase_id,
        payment_method=payment_method,
    )
