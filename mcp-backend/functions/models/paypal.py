from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PayPalPayerInfo:
    given_name: str
    surname: str
    email: str


@dataclass
class PayPalCaptureInfo:
    capture_id: str
    status: str
    final_capture: bool
    amount_value: str
    currency_code: str
    create_time: str
    paypal_fee: str
    net_amount: str


@dataclass
class PayPalOrderInfo:
    order_id: str
    status: str
    payment_method: str
    payer: PayPalPayerInfo
    capture: PayPalCaptureInfo

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PayPalOrderInfo":
        payment_source = payload.get("payment_source") or {}
        method_used = list(payment_source.keys())[0] if payment_source else "unknown"
        method_data = payment_source.get(method_used, {}) if isinstance(payment_source, dict) else {}

        if method_used == "paypal":
            name_info = method_data.get("name", {})
            payer_name = name_info.get("given_name", "")
            payer_surname = name_info.get("surname", "")
            email = method_data.get("email_address", "")
        elif method_used == "apple_pay":
            full_name = method_data.get("name", "")
            name_parts = full_name.split(" ")
            payer_name = name_parts[0] if len(name_parts) > 0 else ""
            payer_surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            email = method_data.get("email_address", "")
        else:
            payer = payload.get("payer", {})
            name_info = payer.get("name", {})
            payer_name = name_info.get("given_name", "")
            payer_surname = name_info.get("surname", "")
            email = payer.get("email_address", "")

        purchase_units = payload.get("purchase_units") or []
        pu = purchase_units[0] if purchase_units else {}
        captures = (pu.get("payments") or {}).get("captures") or []
        capture = captures[0] if captures else {}

        seller_breakdown = capture.get("seller_receivable_breakdown") or {}
        paypal_fee = (seller_breakdown.get("paypal_fee") or {}).get("value", "")
        net_amount = (seller_breakdown.get("net_amount") or {}).get("value", "")
        amount = capture.get("amount") or {}

        capture_info = PayPalCaptureInfo(
            capture_id=capture.get("id", ""),
            status=(capture.get("status") or "").upper(),
            final_capture=bool(capture.get("final_capture", False)),
            amount_value=amount.get("value", ""),
            currency_code=amount.get("currency_code", ""),
            create_time=capture.get("create_time", ""),
            paypal_fee=paypal_fee,
            net_amount=net_amount,
        )

        payer_info = PayPalPayerInfo(
            given_name=payer_name,
            surname=payer_surname,
            email=email,
        )

        return cls(
            order_id=payload.get("id", ""),
            status=(payload.get("status") or "").upper(),
            payment_method=method_used,
            payer=payer_info,
            capture=capture_info,
        )


@dataclass
class PayPalOrderCreateResponse:
    order_id: str
    status: str
    payload: Dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PayPalOrderCreateResponse":
        return cls(
            order_id=payload.get("id", ""),
            status=(payload.get("status") or "").upper(),
            payload=payload,
        )
