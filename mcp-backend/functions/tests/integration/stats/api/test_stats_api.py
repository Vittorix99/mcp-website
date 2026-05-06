import pytest

from api.admin import stats_api
from config.firebase_config import db
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_stats_api_general_stats(create_stats_fixtures):
    """Returns general stats via admin API."""
    create_stats_fixtures()
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(stats_api.admin_get_general_stats(req))
    assert status == 200
    assert "total_events" in resp
    assert "total_purchases" in resp


@pytest.mark.integration
def test_stats_api_snapshot_endpoints(create_stats_fixtures):
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    analytics_service = AnalyticsSnapshotService()
    analytics_service.rebuild_all_snapshots()

    dashboard_resp, dashboard_status = unwrap_response(
        stats_api.admin_get_dashboard_snapshot(DummyRequest(method="GET"))
    )
    assert dashboard_status == 200
    assert "kpis" in dashboard_resp

    event_resp, event_status = unwrap_response(
        stats_api.admin_get_analytics_event_snapshot(
            DummyRequest(method="GET", args={"event_id": event_id})
        )
    )
    assert event_status == 200
    assert event_resp.get("event_id") == event_id
    assert "charts" in event_resp

    global_resp, global_status = unwrap_response(
        stats_api.admin_get_analytics_global_snapshot(DummyRequest(method="GET"))
    )
    assert global_status == 200
    assert "kpis" in global_resp

    index_resp, index_status = unwrap_response(
        stats_api.admin_get_analytics_events_index(DummyRequest(method="GET"))
    )
    assert index_status == 200
    assert any(item.get("event_id") == event_id for item in index_resp.get("events", []))

    flow_resp, flow_status = unwrap_response(
        stats_api.admin_get_entrance_flow(DummyRequest(method="GET", args={"event_id": event_id}))
    )
    assert flow_status == 200
    assert "buckets" in flow_resp
    assert flow_resp.get("totalScanned") == 0
    assert len(flow_resp.get("buckets", [])) == 12
    assert flow_resp.get("buckets", [{}])[0].get("hourLabel") == "21:00"


@pytest.mark.integration
def test_stats_api_rebuild_endpoint_enqueues_job(create_stats_fixtures):
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    req = DummyRequest(method="POST", json={"scope": "event", "event_id": event_id})
    resp, status = unwrap_response(stats_api.admin_rebuild_analytics(req))

    assert status == 202
    assert resp.get("ok") is True
    assert resp.get("job_id")
    assert resp.get("scope") == "event"

    db.collection("analytics_jobs").document(resp.get("job_id")).delete()
