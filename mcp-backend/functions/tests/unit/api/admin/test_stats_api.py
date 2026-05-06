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


def test_admin_get_entrance_flow_forwards_window_params(monkeypatch):
    captured = {}

    class _FakeFlow:
        def model_dump(self, by_alias=True):
            return {
                "eventId": "evt-1",
                "eventTitle": "Test Event",
                "totalScanned": 0,
                "buckets": [],
            }

    def _fake_get_entrance_flow(event_id, start_time=None, span_hours=6, bucket_minutes=30):
        captured["event_id"] = event_id
        captured["start_time"] = start_time
        captured["span_hours"] = span_hours
        captured["bucket_minutes"] = bucket_minutes
        return _FakeFlow()

    monkeypatch.setattr(
        stats_api,
        "analytics_service",
        types.SimpleNamespace(get_entrance_flow=_fake_get_entrance_flow),
    )

    req = DummyRequest(
        method="GET",
        args={
            "event_id": "evt-1",
            "start_time": "21:30",
            "span_hours": "8",
            "bucket_minutes": "15",
        },
    )
    resp, status = unwrap_response(stats_api.admin_get_entrance_flow(req))

    assert status == 200
    assert resp["eventId"] == "evt-1"
    assert captured == {
        "event_id": "evt-1",
        "start_time": "21:30",
        "span_hours": 8,
        "bucket_minutes": 15,
    }


def test_admin_get_entrance_flow_rejects_invalid_bucket_minutes():
    req = DummyRequest(
        method="GET",
        args={"event_id": "evt-1", "bucket_minutes": "7"},
    )
    resp, status = unwrap_response(stats_api.admin_get_entrance_flow(req))

    assert status == 400
    assert resp["error"] == "Invalid request data"
