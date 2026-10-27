from decimal import Decimal

import pytest
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest

from config.runtime_settings import RuntimeConfigurationError, load_runtime_settings
from services.payments.paypal_gateway import FakePayPalGateway, build_paypal_gateway
from tests.config_fixtures import cloud_environment


def _request():
    return OrderRequest(intent=CheckoutPaymentIntent.CAPTURE, purchase_units=[
        PurchaseUnitRequest(reference_id="event-1", amount=AmountWithBreakdown(currency_code="EUR", value="12.50"))
    ])


@pytest.mark.parametrize("environment", ["local", "test"])
def test_fake_order_and_capture_preserve_amount_without_sdk(environment, monkeypatch):
    import services.payments.paypal_gateway as module
    monkeypatch.setattr(module, "PaypalServersdkClient", lambda **kwargs: pytest.fail("SDK must remain unused"))
    gateway = build_paypal_gateway(load_runtime_settings({"MCP_ENV": environment}))
    assert isinstance(gateway, FakePayPalGateway)
    created = gateway.create_order(_request())
    assert created.payload["id"].startswith("FAKE-")
    captured = gateway.capture_order(created.payload["id"])
    capture = captured.payload["purchase_units"][0]["payments"]["captures"][0]
    assert captured.status_code == 201
    assert captured.payload["status"] == "COMPLETED"
    assert Decimal(capture["amount"]["value"]) == Decimal("12.50")
    assert capture["amount"]["currency_code"] == "EUR"
    assert gateway.capture_order(created.payload["id"]).payload == captured.payload


def test_fake_capture_of_unknown_order_cannot_look_successful():
    gateway = build_paypal_gateway(load_runtime_settings({"MCP_ENV": "test"}))
    assert gateway.capture_order("FAKE-UNKNOWN").status_code == 404


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_cloud_gateway_requires_credentials_without_echoing_values(environment):
    settings = load_runtime_settings({**cloud_environment(environment), "PAYPAL_CLIENT_ID": "SENTINEL_ID"})
    settings = settings.model_copy(update={"providers": settings.providers.model_copy(update={"paypal_client_secret": None})})
    with pytest.raises(RuntimeConfigurationError) as error:
        build_paypal_gateway(settings)
    assert "SENTINEL_ID" not in str(error.value)


@pytest.mark.parametrize("environment,want", [("staging", "Sandbox"), ("production", "Production")])
def test_sdk_environment_is_selected_only_from_validated_mode(environment, want, monkeypatch):
    import services.payments.paypal_gateway as module
    configured = []
    class Client:
        def __init__(self, **kwargs):
            configured.append(kwargs)
            self.orders = object()
    monkeypatch.setattr(module, "PaypalServersdkClient", Client)
    settings = load_runtime_settings({**cloud_environment(environment),
        "PAYPAL_CLIENT_ID": "SENTINEL_ID", "PAYPAL_CLIENT_SECRET": "SENTINEL_SECRET"})
    build_paypal_gateway(settings)
    expected = module.Environment.SANDBOX if environment == "staging" else module.Environment.PRODUCTION
    assert configured[0]["environment"] == expected
