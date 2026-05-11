import pytest

from api.admin import stats_api
from config.firebase_config import db
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from tests.utils import DummyRequest, unwrap_response


# ---------------------------------------------------------------------------
# General stats
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_general_stats_returns_correct_counts(create_stats_fixtures):
    """General stats reflect seeded data: at least 1 event, purchase, member."""
    create_stats_fixtures()
    resp, status = unwrap_response(stats_api.admin_get_general_stats(DummyRequest(method="GET")))
    assert status == 200
    assert resp.get("total_events", 0) >= 1
    assert resp.get("total_purchases", 0) >= 1
    assert resp.get("total_active_members", 0) >= 1
    assert resp.get("last_participant") is not None
    assert resp.get("last_purchase") is not None
    assert resp.get("last_membership") is not None


# ---------------------------------------------------------------------------
# Event snapshot: create → retrieve via API
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_event_snapshot_api_create_and_retrieve(create_stats_fixtures):
    """Build event snapshot then retrieve it via API: kpis and charts must be populated."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    AnalyticsSnapshotService().rebuild_event_snapshot(event_id)

    resp, status = unwrap_response(
        stats_api.admin_get_analytics_event_snapshot(
            DummyRequest(method="GET", args={"event_id": event_id})
        )
    )
    assert status == 200
    assert resp.get("event_id") == event_id
    assert resp.get("exists") is True

    kpis = resp.get("kpis") or {}
    assert kpis.get("participants") == 1
    assert kpis.get("entered") == 0
    assert "revenue_gross" in kpis
    assert "revenue_net" in kpis
    assert "omaggi" in kpis

    charts = resp.get("charts") or {}
    assert "entrance_flow" in charts
    assert "gender_distribution" in charts
    assert "membership_trend" in charts


@pytest.mark.integration
def test_event_snapshot_api_no_snapshot_returns_exists_false(create_stats_fixtures):
    """Requesting an event snapshot that was never built returns exists=False (no 404)."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    # Ensure no snapshot exists for this event
    db.collection("analytics_event").document(event_id).delete()

    resp, status = unwrap_response(
        stats_api.admin_get_analytics_event_snapshot(
            DummyRequest(method="GET", args={"event_id": event_id})
        )
    )
    assert status == 200
    assert resp.get("exists") is False
    assert resp.get("event_id") == event_id


@pytest.mark.integration
def test_event_snapshot_api_missing_event_id_returns_400():
    """Missing event_id query param returns 400."""
    resp, status = unwrap_response(
        stats_api.admin_get_analytics_event_snapshot(DummyRequest(method="GET", args={}))
    )
    assert status == 400


# ---------------------------------------------------------------------------
# Dashboard snapshot: create → retrieve via API
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_dashboard_snapshot_api_create_and_retrieve(create_stats_fixtures):
    """Build global+dashboard snapshot then retrieve via API: kpis must be correct."""
    create_stats_fixtures()
    service = AnalyticsSnapshotService()
    service.rebuild_global_snapshot()
    service.rebuild_dashboard_snapshot()

    resp, status = unwrap_response(
        stats_api.admin_get_dashboard_snapshot(DummyRequest(method="GET"))
    )
    assert status == 200
    assert resp.get("exists") is True

    kpis = resp.get("kpis") or {}
    assert kpis.get("events", 0) >= 1
    assert kpis.get("active_members", 0) >= 1
    assert kpis.get("unique_participants", 0) >= 1
    assert "total_revenue_net" in kpis
    assert "avg_fill_rate" in kpis
    assert "this_month_revenue" in kpis


@pytest.mark.integration
def test_dashboard_snapshot_api_no_snapshot_returns_exists_false():
    """If dashboard snapshot was never built, API returns exists=False."""
    db.collection("analytics_dashboard").document("current").delete()

    resp, status = unwrap_response(
        stats_api.admin_get_dashboard_snapshot(DummyRequest(method="GET"))
    )
    assert status == 200
    assert resp.get("exists") is False


# ---------------------------------------------------------------------------
# Global snapshot: create → retrieve via API
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_global_snapshot_api_create_and_retrieve(create_stats_fixtures):
    """Build global snapshot then retrieve via API: kpis and charts must be populated."""
    create_stats_fixtures()
    AnalyticsSnapshotService().rebuild_global_snapshot()

    resp, status = unwrap_response(
        stats_api.admin_get_analytics_global_snapshot(DummyRequest(method="GET"))
    )
    assert status == 200
    assert resp.get("exists") is True

    kpis = resp.get("kpis") or {}
    assert "avg_unit_payment" in kpis
    assert "gender_distribution" in kpis
    assert "age_band_dominant" in kpis

    charts = resp.get("charts") or {}
    assert "age_bands_distribution" in charts
    assert "gender_distribution" in charts


@pytest.mark.integration
def test_global_snapshot_api_no_snapshot_returns_exists_false():
    """If global snapshot was never built, API returns exists=False."""
    db.collection("analytics_global").document("current").delete()

    resp, status = unwrap_response(
        stats_api.admin_get_analytics_global_snapshot(DummyRequest(method="GET"))
    )
    assert status == 200
    assert resp.get("exists") is False


# ---------------------------------------------------------------------------
# Events index
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_events_index_api_contains_created_event(create_stats_fixtures):
    """Events index lists every event that has a snapshot, with title and date."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    AnalyticsSnapshotService().rebuild_event_snapshot(event_id)

    resp, status = unwrap_response(
        stats_api.admin_get_analytics_events_index(DummyRequest(method="GET"))
    )
    assert status == 200
    events = resp.get("events", [])
    ids = [item.get("event_id") for item in events]
    assert event_id in ids

    entry = next(item for item in events if item["event_id"] == event_id)
    assert entry.get("title")
    assert entry.get("date")


# ---------------------------------------------------------------------------
# Rebuild endpoint
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_rebuild_api_full_cycle(create_stats_fixtures):
    """POST rebuild(scope=event) enqueues a job; after processing, snapshot is retrievable."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    req = DummyRequest(method="POST", json={"scope": "event", "event_id": event_id})
    resp, status = unwrap_response(stats_api.admin_rebuild_analytics(req))
    assert status == 202
    assert resp.get("ok") is True
    job_id = resp.get("job_id")
    assert job_id
    assert resp.get("scope") == "event"

    try:
        # Process the job synchronously (normally done by Firestore trigger)
        AnalyticsSnapshotService().process_rebuild_job(job_id)

        job_data = db.collection("analytics_jobs").document(job_id).get().to_dict() or {}
        assert job_data.get("status") == "completed"

        # Snapshot must now be retrievable via API
        event_resp, event_status = unwrap_response(
            stats_api.admin_get_analytics_event_snapshot(
                DummyRequest(method="GET", args={"event_id": event_id})
            )
        )
        assert event_status == 200
        assert event_resp.get("exists") is True
        assert (event_resp.get("kpis") or {}).get("participants") == 1
    finally:
        db.collection("analytics_jobs").document(job_id).delete()


@pytest.mark.integration
def test_rebuild_api_scope_event_without_event_id_returns_400():
    """scope=event without event_id returns 400."""
    req = DummyRequest(method="POST", json={"scope": "event"})
    resp, status = unwrap_response(stats_api.admin_rebuild_analytics(req))
    assert status == 400


@pytest.mark.integration
def test_rebuild_api_wrong_method_returns_405():
    """GET on rebuild endpoint returns 405."""
    resp, status = unwrap_response(stats_api.admin_rebuild_analytics(DummyRequest(method="GET")))
    assert status == 405


# ---------------------------------------------------------------------------
# Entrance flow
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_entrance_flow_api_structure(create_stats_fixtures):
    """Entrance flow returns 12 buckets of 30min starting at event startTime, 0 scans."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]  # startTime="21:00", default span=6h

    resp, status = unwrap_response(
        stats_api.admin_get_entrance_flow(
            DummyRequest(method="GET", args={"event_id": event_id})
        )
    )
    assert status == 200
    assert resp.get("totalScanned") == 0
    buckets = resp.get("buckets", [])
    assert len(buckets) == 12
    assert buckets[0].get("hourLabel") == "21:00"


@pytest.mark.integration
def test_entrance_flow_api_missing_event_id_returns_400():
    """Missing event_id for entrance flow returns 400."""
    resp, status = unwrap_response(
        stats_api.admin_get_entrance_flow(DummyRequest(method="GET", args={}))
    )
    assert status == 400
