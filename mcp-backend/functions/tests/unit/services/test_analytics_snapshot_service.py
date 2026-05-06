from types import SimpleNamespace

from services.core.analytics_snapshot_service import AnalyticsSnapshotService


class _DummyRepo:
    def stream_models(self):
        return iter(())


class _JobRepo:
    def __init__(self, rows=None):
        self.created_model = None
        self.updates = []
        self.rows = rows or []

    def stream_raw_by_type(self, _job_type):
        return iter(self.rows)

    def create_from_model(self, job):
        self.created_model = job
        return "job-analytics-1"

    def update(self, job_id, payload):
        self.updates.append((job_id, payload))


def _service():
    return AnalyticsSnapshotService(
        event_repository=_DummyRepo(),
        membership_repository=_DummyRepo(),
        purchase_repository=_DummyRepo(),
        participant_repository=_DummyRepo(),
        message_repository=_DummyRepo(),
        job_repository=_DummyRepo(),
    )


def test_ticket_tier_mapping_four_distinct_prices():
    service = _service()

    rows = [
        {"purchase_id": "p1", "unit_price": 10.0},
        {"purchase_id": "p2", "unit_price": 15.0},
        {"purchase_id": "p3", "unit_price": 20.0},
        {"purchase_id": "p4", "unit_price": 25.0},
    ]

    mapping = service._map_ticket_tiers(rows)

    assert mapping["p1"] == "super_early"
    assert mapping["p2"] == "early"
    assert mapping["p3"] == "regular"
    assert mapping["p4"] == "late"


def test_ticket_tier_mapping_three_distinct_prices():
    service = _service()

    rows = [
        {"purchase_id": "p1", "unit_price": 12.0},
        {"purchase_id": "p2", "unit_price": 18.0},
        {"purchase_id": "p3", "unit_price": 24.0},
    ]

    mapping = service._map_ticket_tiers(rows)

    assert mapping["p1"] == "early"
    assert mapping["p2"] == "regular"
    assert mapping["p3"] == "late"


def test_ticket_tier_mapping_tolerance_clusters_close_prices():
    service = _service()

    rows = [
        {"purchase_id": "p1", "unit_price": 20.0},
        {"purchase_id": "p2", "unit_price": 20.3},  # same tier due to tolerance 0.50
        {"purchase_id": "p3", "unit_price": 27.0},
    ]

    mapping = service._map_ticket_tiers(rows)

    assert mapping["p1"] == mapping["p2"]
    assert mapping["p3"] in {"regular", "late"}


def test_ticket_tier_payload_aggregates_counts_and_amounts():
    service = _service()

    purchases = [
        SimpleNamespace(id="a", participants_count=2, amount_total="20.00", net_amount="18.00"),
        SimpleNamespace(id="b", participants_count=3, amount_total="36.00", net_amount="32.00"),
    ]

    payload = service._build_ticket_tier_payload(purchases)

    assert "tiers" in payload
    assert "chart" in payload
    assert sum(item["count"] for item in payload["tiers"]) == 5
    assert round(sum(item["gross"] for item in payload["tiers"]), 2) == 56.00


def test_enqueue_full_rebuild_creates_complete_job_payload():
    job_repo = _JobRepo()
    service = AnalyticsSnapshotService(
        event_repository=_DummyRepo(),
        membership_repository=_DummyRepo(),
        purchase_repository=_DummyRepo(),
        participant_repository=_DummyRepo(),
        message_repository=_DummyRepo(),
        job_repository=job_repo,
        entrance_scan_repository=_DummyRepo(),
        analytics_snapshot_repository=SimpleNamespace(),
    )

    result = service.enqueue_full_rebuild(reason="manual:test")

    assert result["job_id"] == "job-analytics-1"
    assert result["scope"] == "all"
    assert job_repo.created_model.type == "analytics_rebuild"
    assert job_repo.created_model.status == "queued"
    assert job_repo.created_model.scope == "all"
    assert job_repo.created_model.reason == "manual:test"
    assert job_repo.created_model.updated_at is not None


def test_enqueue_full_rebuild_kicks_existing_queued_job():
    job_repo = _JobRepo(rows=[("queued-job", {"type": "analytics_rebuild", "status": "queued", "scope": "all"})])
    service = AnalyticsSnapshotService(
        event_repository=_DummyRepo(),
        membership_repository=_DummyRepo(),
        purchase_repository=_DummyRepo(),
        participant_repository=_DummyRepo(),
        message_repository=_DummyRepo(),
        job_repository=job_repo,
        entrance_scan_repository=_DummyRepo(),
        analytics_snapshot_repository=SimpleNamespace(),
    )

    result = service.enqueue_full_rebuild(reason="manual:test")

    assert result["job_id"] == "queued-job"
    assert result["deduped"] is True
    assert result["kicked"] is True
    assert job_repo.created_model is None
    assert job_repo.updates[0][0] == "queued-job"
    assert job_repo.updates[0][1]["last_kicked_at"] is not None
