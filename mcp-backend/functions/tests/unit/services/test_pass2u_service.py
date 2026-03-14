from types import SimpleNamespace

from models import Membership
from services.memberships.pass2u_service import Pass2UService


def _membership(end_date="31-12-2026"):
    return Membership(
        name="Mario",
        surname="Rossi",
        email="mario@example.com",
        end_date=end_date,
    )


def test_create_membership_pass_success(monkeypatch):
    service = Pass2UService()
    captured = {}

    monkeypatch.setattr(service, "_get_model_id", lambda: "371225")
    monkeypatch.setattr("services.memberships.pass2u_service.PASS2U_API_KEY", "api-key")
    monkeypatch.setattr(
        "services.memberships.pass2u_service.to_iso8601_datetime",
        lambda value: "2026-12-31T23:59:59+00:00",
    )

    def fake_create_pass(model_id, api_key, body):
        captured["model_id"] = model_id
        captured["api_key"] = api_key
        captured["body"] = body
        return SimpleNamespace(status_code=201, ok=True, payload={"passId": "pass-123"}, error_message=None)

    monkeypatch.setattr("services.memberships.pass2u_service.Pass2URoutes.create_pass", fake_create_pass)

    result = service.create_membership_pass("mem-1", _membership())

    assert result is not None
    assert result.pass_id == "pass-123"
    assert result.wallet_url.endswith("/pass-123")
    assert captured["model_id"] == "371225"
    assert captured["api_key"] == "api-key"
    assert captured["body"]["expirationDate"] == "2026-12-31T23:59:59+00:00"
    assert {"key": "mail", "value": "mario@example.com"} in captured["body"]["fields"]


def test_create_membership_pass_returns_none_on_bad_response(monkeypatch):
    service = Pass2UService()
    monkeypatch.setattr(service, "_get_model_id", lambda: "371225")
    monkeypatch.setattr("services.memberships.pass2u_service.PASS2U_API_KEY", "api-key")
    monkeypatch.setattr(
        "services.memberships.pass2u_service.Pass2URoutes.create_pass",
        lambda **kwargs: SimpleNamespace(status_code=200, ok=True, payload={}, error_message=None),
    )

    result = service.create_membership_pass("mem-1", _membership())
    assert result is None


def test_create_membership_pass_returns_none_on_conflict(monkeypatch):
    service = Pass2UService()
    monkeypatch.setattr(service, "_get_model_id", lambda: "371225")
    monkeypatch.setattr("services.memberships.pass2u_service.PASS2U_API_KEY", "api-key")
    monkeypatch.setattr(
        "services.memberships.pass2u_service.Pass2URoutes.create_pass",
        lambda **kwargs: SimpleNamespace(status_code=409, ok=False, payload={}, error_message="conflict"),
    )

    result = service.create_membership_pass("mem-1", _membership())
    assert result is None


def test_invalidate_membership_pass_handles_404_as_success(monkeypatch):
    service = Pass2UService()
    monkeypatch.setattr("services.memberships.pass2u_service.PASS2U_API_KEY", "api-key")
    monkeypatch.setattr(
        "services.memberships.pass2u_service.Pass2URoutes.invalidate_pass",
        lambda **kwargs: SimpleNamespace(status_code=404, ok=False, payload={}, error_message="not found"),
    )

    assert service.invalidate_membership_pass("pass-123") is True


def test_invalidate_membership_pass_failure(monkeypatch):
    service = Pass2UService()
    monkeypatch.setattr("services.memberships.pass2u_service.PASS2U_API_KEY", "api-key")
    monkeypatch.setattr(
        "services.memberships.pass2u_service.Pass2URoutes.invalidate_pass",
        lambda **kwargs: SimpleNamespace(status_code=500, ok=False, payload={}, error_message="boom"),
    )

    assert service.invalidate_membership_pass("pass-123") is False
