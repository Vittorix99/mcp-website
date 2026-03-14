import types

from api.admin import stats_api
from errors.service_errors import ExternalServiceError
from tests.utils import DummyRequest, unwrap_response


def test_admin_get_general_stats_invalid_method():
    """Rejects invalid method."""
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(stats_api.admin_get_general_stats(req))
    assert status == 405


def test_admin_get_general_stats_happy_path(monkeypatch):
    """Returns stats payload."""
    monkeypatch.setattr(
        stats_api,
        "stats_service",
        types.SimpleNamespace(get_general_stats=lambda: {"ok": True}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(stats_api.admin_get_general_stats(req))
    assert status == 200
    assert resp["ok"] is True


def test_admin_get_general_stats_external_error(monkeypatch):
    """Maps external errors to 502."""
    monkeypatch.setattr(
        stats_api,
        "stats_service",
        types.SimpleNamespace(get_general_stats=lambda: (_ for _ in ()).throw(ExternalServiceError("boom"))),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(stats_api.admin_get_general_stats(req))
    assert status == 502
    assert resp["error"] == "boom"
