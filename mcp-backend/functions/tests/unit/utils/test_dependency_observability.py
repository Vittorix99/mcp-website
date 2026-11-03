import json
from types import SimpleNamespace
from uuid import UUID

from flask import Flask, jsonify, request
import pytest

from clients.mailersend_client import MailerSendRequest, MailerSendRoutes
from services.payments.paypal_gateway import SdkPayPalGateway
from utils import http_observability as obs


FIELDS = {"event", "severity", "environment", "provider", "operation", "request_id",
          "status_code", "outcome", "duration_ms"}
SENTINEL = "sentinel-order-9f3a@example.test"


class Orders:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error
        self.calls = []

    def orders_create(self, args):
        return self._reply(("create", args))

    def orders_capture(self, args):
        return self._reply(("capture", args))

    def _reply(self, call):
        self.calls.append(call)
        if self.error:
            raise self.error
        return self.result


class MailClient:
    def __init__(self, response=None, error=None):
        self.emails = SimpleNamespace(send=self._send)
        self.response, self.error = response, error

    def _send(self, _raw):
        if self.error:
            raise self.error
        return self.response


class Builder:
    def __getattr__(self, name):
        return (lambda *a, **k: self) if name != "build" else (lambda: {})


def _records(capfd):
    return [json.loads(line) for line in capfd.readouterr().out.splitlines()
            if '"dependency_completed"' in line]


def _mail(response=None, error=None):
    mail = MailerSendRequest("a@example.test", SENTINEL, "subject", "body")
    return MailerSendRoutes.send_email(
        mail, "key", client_cls=lambda _k: MailClient(response, error), builder_cls=Builder)


def _paypal(orders):
    return SdkPayPalGateway(orders_controller=orders)


def _ok(code=201):
    return SimpleNamespace(status_code=code, body={"id": SENTINEL})


def test_paypal_create_and_capture_record_provider_operation_status_and_outcome(capfd):
    orders = Orders(_ok())
    gateway = _paypal(orders)
    gateway.create_order({"x": 1})
    gateway.capture_order("ORDER-1")
    first, second = _records(capfd)
    assert set(first) == FIELDS
    assert (first["provider"], first["operation"]) == ("paypal", "create_order")
    assert (second["provider"], second["operation"]) == ("paypal", "capture_order")
    assert first["status_code"] == 201 and first["outcome"] == "success"
    assert first["request_id"] is None and first["environment"] == "test"
    assert first["duration_ms"] >= 0 and first["severity"] == "INFO"
    assert [c[0] for c in orders.calls] == ["create", "capture"]
    assert orders.calls[1][1]["paypal_request_id"] == "mcp-capture-ORDER-1"
    assert "ORDER-1" not in json.dumps([first, second])


def test_paypal_returned_error_and_exception_preserve_behavior(capfd):
    assert _paypal(Orders(_ok(422))).create_order({}).status_code == 422
    failure = RuntimeError(f"boom {SENTINEL}")
    with pytest.raises(RuntimeError) as raised:
        _paypal(Orders(error=failure)).capture_order("ORDER-2")
    assert raised.value is failure
    error, exception = _records(capfd)
    assert (error["outcome"], error["status_code"], error["severity"]) == ("error", 422, "WARNING")
    assert (exception["outcome"], exception["status_code"], exception["severity"]) == ("exception", None, "ERROR")
    assert SENTINEL not in json.dumps([error, exception]) and "ORDER-2" not in json.dumps(exception)


def test_mailersend_success_error_and_swallowed_exception_are_recorded_without_recipient(capfd):
    ok = _mail(SimpleNamespace(status_code=202, success=True, data={"id": SENTINEL}))
    bad = _mail(SimpleNamespace(status_code=422, success=False, data={"message": SENTINEL}))
    raised = _mail(error=RuntimeError(SENTINEL))
    assert (ok.success, bad.success, raised.success) == (True, False, False)
    assert raised.error_message == SENTINEL  # result contract is unchanged
    success, error, exception = _records(capfd)
    assert (success["provider"], success["operation"]) == ("mailersend", "send_email")
    assert [r["outcome"] for r in (success, error, exception)] == ["success", "error", "error"]
    assert [r["status_code"] for r in (success, error, exception)] == [202, 422, None]
    assert SENTINEL not in json.dumps([success, error, exception])


def test_request_id_is_shared_with_http_record_separate_per_request_and_restored(capfd):
    app = Flask("dependency")
    gateway = _paypal(Orders(_ok()))

    def handler(_req):
        gateway.create_order({})
        return jsonify({})

    observed = obs.observe_http_request(handler)
    app.add_url_rule("/p", view_func=lambda: observed(request))
    client = app.test_client()
    ids = []
    for _ in range(2):
        response = client.get("/p")
        dependency = _records_from(capfd.readouterr().out)
        assert dependency["request_id"] == response.headers["X-Request-ID"]
        ids.append(dependency["request_id"])
    assert ids[0] != ids[1] and UUID(ids[0]).version == 4
    gateway.create_order({})
    assert _records(capfd)[0]["request_id"] is None


def _records_from(out):
    lines = [json.loads(line) for line in out.splitlines()]
    dependency = [r for r in lines if r["event"] == "dependency_completed"]
    assert len(dependency) == 1 and len(lines) == 2
    return dependency[0]


def test_request_context_is_restored_after_handler_exception():
    app = Flask("dependency-failure")

    def handler(_req):
        raise RuntimeError("x")

    observed = obs.observe_http_request(handler)
    app.add_url_rule("/p", view_func=lambda: observed(request))
    app.testing = True
    with pytest.raises(RuntimeError):
        app.test_client().get("/p")
    assert obs._current_request_id.get() is None


def test_writer_failure_never_changes_result_or_exception(monkeypatch):
    def broken(*_a, **_k):
        raise OSError("stdout closed")

    monkeypatch.setattr("builtins.print", broken)
    assert _paypal(Orders(_ok())).create_order({}).status_code == 201
    with pytest.raises(RuntimeError, match="original"):
        _paypal(Orders(error=RuntimeError("original"))).create_order({})
    assert _mail(SimpleNamespace(status_code=202, success=True, data=None)).success is True


class ApiError(Exception):
    def __init__(self, response_code):
        super().__init__("provider failure")
        self.response_code = response_code


@pytest.mark.parametrize("code,expected", [(422, 422), ("x", None), (999, None)])
def test_exception_status_comes_only_from_a_valid_response_code(capfd, code, expected):
    with pytest.raises(ApiError):
        _paypal(Orders(error=ApiError(code))).create_order({})
    record = _records(capfd)[0]
    assert (record["outcome"], record["status_code"]) == ("exception", expected)


def test_classification_failure_keeps_the_valid_result(capfd):
    result = object()
    assert obs.timed_dependency("p", "o", lambda: result, lambda r: r.status_code) is result
    assert _records(capfd)[0]["outcome"] == "error"


def test_send_email_accepts_client_and_builder_positionally():
    mail = MailerSendRequest("a@example.test", SENTINEL, "subject", "body")
    response = SimpleNamespace(status_code=202, success=True, data=None)
    result = MailerSendRoutes.send_email(mail, "key", lambda _k: MailClient(response), Builder)
    assert result.success is True


@pytest.mark.parametrize("target", ["get_runtime_settings", "dumps"])
def test_other_writer_failures_never_change_result_or_exception(monkeypatch, target):
    def broken(*_a, **_k):
        raise OSError("unavailable")

    if target == "dumps":
        monkeypatch.setattr(obs.json, "dumps", broken)
    else:
        monkeypatch.setattr(obs, target, broken)
    assert _paypal(Orders(_ok())).create_order({}).status_code == 201
    with pytest.raises(RuntimeError, match="original"):
        _paypal(Orders(error=RuntimeError("original"))).create_order({})
