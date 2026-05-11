import pytest

from config.firebase_config import db
from services.core.analytics_snapshot_service import AnalyticsSnapshotService


@pytest.mark.integration
def test_analytics_snapshot_build_base(create_stats_fixtures):
    """rebuild_event/global/dashboard_snapshot writes documents to Firestore."""
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


@pytest.mark.integration
def test_event_snapshot_kpis_reflect_participants(create_stats_fixtures):
    """KPIs in event snapshot reflect actual participant data seeded by fixtures."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    service = AnalyticsSnapshotService()
    result = service.rebuild_event_snapshot(event_id)

    assert result.get("event_id") == event_id
    kpis = result.get("kpis") or {}
    assert kpis.get("participants") == 1
    assert kpis.get("entered") == 0
    assert "omaggi" in kpis
    assert "revenue_gross" in kpis
    assert "revenue_net" in kpis

    charts = result.get("charts") or {}
    assert "entrance_flow" in charts
    assert "gender_distribution" in charts
    assert "membership_trend" in charts


@pytest.mark.integration
def test_global_snapshot_has_gender_and_age(create_stats_fixtures):
    """Global snapshot kpis include gender_distribution and age_band_dominant."""
    create_stats_fixtures()

    service = AnalyticsSnapshotService()
    result = service.rebuild_global_snapshot()

    kpis = result.get("kpis") or {}
    assert "gender_distribution" in kpis
    assert "age_band_dominant" in kpis
    assert "avg_unit_payment" in kpis

    charts = result.get("charts") or {}
    assert "age_bands_distribution" in charts
    assert "gender_distribution" in charts


@pytest.mark.integration
def test_dashboard_snapshot_kpis_are_consistent(create_stats_fixtures):
    """Dashboard snapshot kpis are numerically consistent with seeded data."""
    create_stats_fixtures()

    service = AnalyticsSnapshotService()
    service.rebuild_global_snapshot()
    result = service.rebuild_dashboard_snapshot()

    kpis = result.get("kpis") or {}
    assert kpis.get("events", 0) >= 1
    assert kpis.get("active_members", 0) >= 1
    assert kpis.get("unique_participants", 0) >= 1
    assert "total_revenue_net" in kpis
    assert "avg_fill_rate" in kpis


@pytest.mark.integration
def test_events_index_contains_created_event(create_stats_fixtures):
    """get_events_index returns an entry for every event that has a snapshot."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    service = AnalyticsSnapshotService()
    service.rebuild_event_snapshot(event_id)

    index = service.get_events_index()
    event_ids = [item.get("event_id") for item in index.get("events", [])]
    assert event_id in event_ids

    entry = next(item for item in index["events"] if item["event_id"] == event_id)
    assert entry.get("title")
    assert entry.get("date")


@pytest.mark.integration
def test_process_rebuild_job_completes(create_stats_fixtures):
    """process_rebuild_job transitions a queued analytics job to completed."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    service = AnalyticsSnapshotService()
    enqueue_result = service.enqueue_event_rebuild(event_id, reason="integration-test")
    job_id = enqueue_result.get("job_id")
    assert job_id, "enqueue_event_rebuild must return a job_id"

    try:
        service.process_rebuild_job(job_id)

        job_data = db.collection("analytics_jobs").document(job_id).get().to_dict() or {}
        assert job_data.get("status") == "completed"
        assert job_data.get("percent") == 100
        assert job_data.get("error") is None

        event_snap = db.collection("analytics_event").document(event_id).get()
        assert event_snap.exists
    finally:
        db.collection("analytics_jobs").document(job_id).delete()


@pytest.mark.integration
def test_enqueue_deduplicates_queued_jobs(create_stats_fixtures):
    """Enqueuing twice for the same event returns the same job_id (dedup)."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    service = AnalyticsSnapshotService()
    first = service.enqueue_event_rebuild(event_id, reason="first")
    second = service.enqueue_event_rebuild(event_id, reason="second")

    job_id = first.get("job_id")
    try:
        assert first.get("job_id") == second.get("job_id"), "Second enqueue must reuse the queued job"
        assert second.get("deduped") is True
    finally:
        if job_id:
            db.collection("analytics_jobs").document(job_id).delete()


@pytest.mark.integration
def test_rebuild_all_snapshots(create_stats_fixtures):
    """rebuild_all_snapshots processes all events and writes global + dashboard."""
    fixtures = create_stats_fixtures()
    event_id = fixtures["events"][0]

    service = AnalyticsSnapshotService()
    result = service.rebuild_all_snapshots()

    assert result.get("ok") is True
    assert result.get("events_rebuilt", 0) >= 1

    assert db.collection("analytics_global").document("current").get().exists
    assert db.collection("analytics_dashboard").document("current").get().exists
    assert db.collection("analytics_event").document(event_id).get().exists
