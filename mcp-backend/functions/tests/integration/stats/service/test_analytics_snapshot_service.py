import pytest

from config.firebase_config import db
from services.core.analytics_snapshot_service import AnalyticsSnapshotService


@pytest.mark.integration
def test_analytics_snapshot_build_base(create_stats_fixtures):
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    service = AnalyticsSnapshotService()
    service.rebuild_event_snapshot(event_id)
    service.rebuild_global_snapshot()
    service.rebuild_dashboard_snapshot()

    event_doc = db.collection("analytics_event").document(event_id).get()
    global_doc = db.collection("analytics_global").document("current").get()
    dashboard_doc = db.collection("analytics_dashboard").document("current").get()

    assert event_doc.exists
    assert global_doc.exists
    assert dashboard_doc.exists

    event_payload = event_doc.to_dict() or {}
    global_payload = global_doc.to_dict() or {}
    dashboard_payload = dashboard_doc.to_dict() or {}

    assert "charts" in event_payload
    assert "kpis" in global_payload
    assert "kpis" in dashboard_payload
