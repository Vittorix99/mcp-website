"""PayPal selection is a configuration decision, never a credential fallback."""

from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Protocol

from paypalserversdk.api_helper import ApiHelper
from paypalserversdk.configuration import Environment
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient

from config.runtime_settings import (
    ProviderMode, RuntimeConfigurationError, RuntimeSettings, get_runtime_settings,
)


@dataclass(frozen=True)
class PayPalGatewayResponse:
    status_code: int
    payload: dict


class PayPalGateway(Protocol):
    def create_order(self, request: OrderRequest) -> PayPalGatewayResponse: ...
    def capture_order(self, order_id: str) -> PayPalGatewayResponse: ...


class SdkPayPalGateway:
    def __init__(self, client=None, *, orders_controller=None):
        self._orders = orders_controller if orders_controller is not None else client.orders

    @staticmethod
    def _response(response):
        return PayPalGatewayResponse(response.status_code,
            json.loads(ApiHelper.json_serialize(response.body)))

    def create_order(self, request: OrderRequest) -> PayPalGatewayResponse:
        return self._response(self._orders.orders_create({"body": request}))

    def capture_order(self, order_id: str) -> PayPalGatewayResponse:
        return self._response(self._orders.orders_capture({
            "id": order_id, "prefer": "return=representation",
            "paypal_request_id": f"mcp-capture-{order_id}",
        }))


class FakePayPalGateway:
    def __init__(self):
        self._orders = {}
        self._captures = {}

    def create_order(self, request: OrderRequest) -> PayPalGatewayResponse:
        payload = json.loads(ApiHelper.json_serialize(request))
        order_id = f"FAKE-{len(self._orders) + 1:08d}"
        self._orders[order_id] = payload
        return PayPalGatewayResponse(201, {"id": order_id, "status": "CREATED"})

    def capture_order(self, order_id: str) -> PayPalGatewayResponse:
        if order_id not in self._orders:
            return PayPalGatewayResponse(404, {"error": "Unknown fake order"})
        if order_id not in self._captures:
            units = self._orders[order_id]["purchase_units"]
            self._captures[order_id] = {
                "id": order_id, "status": "COMPLETED",
                "payment_source": {"paypal": {
                    "name": {"given_name": "Local", "surname": "Buyer"},
                    "email_address": "buyer@example.test",
                }},
                "purchase_units": [{"payments": {"captures": [{
                    "id": f"FAKE-CAPTURE-{order_id}", "status": "COMPLETED",
                    "final_capture": True, "amount": deepcopy(units[0]["amount"]),
                    "create_time": "2026-01-01T00:00:00Z",
                    "seller_receivable_breakdown": {
                        "paypal_fee": {"value": "0.00"},
                        "net_amount": deepcopy(units[0]["amount"]),
                    },
                }]}}],
            }
        return PayPalGatewayResponse(201, deepcopy(self._captures[order_id]))


def build_paypal_gateway(settings: RuntimeSettings | None = None) -> PayPalGateway:
    settings = settings or get_runtime_settings()
    provider = settings.providers
    if provider.paypal == ProviderMode.FAKE:
        return FakePayPalGateway()
    if provider.paypal not in {ProviderMode.SANDBOX, ProviderMode.LIVE}:
        raise RuntimeConfigurationError("PayPal mode does not permit checkout")
    if not provider.paypal_client_id or not provider.paypal_client_secret:
        raise RuntimeConfigurationError("PayPal requires client ID and client secret for the selected mode")
    client = PaypalServersdkClient(
        client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
            o_auth_client_id=provider.paypal_client_id.get_secret_value(),
            o_auth_client_secret=provider.paypal_client_secret.get_secret_value(),
        ),
        environment=Environment.SANDBOX if provider.paypal == ProviderMode.SANDBOX else Environment.PRODUCTION,
    )
    return SdkPayPalGateway(client)
