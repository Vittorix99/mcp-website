import types

from triggers import jobs_trigger


def test_process_send_location_job_runs_worker(monkeypatch):
    called = {}

    monkeypatch.setattr(
        jobs_trigger.location_service,
        "_worker_send_location",
        lambda job_id: called.setdefault("job_id", job_id),
    )

    event = types.SimpleNamespace(
        data={"type": "send_location", "status": "queued"},
        params={"jobId": "job-1"},
    )

    jobs_trigger.process_send_location_job.__wrapped__(event)

    assert called.get("job_id") == "job-1"


def test_process_send_location_job_runs_worker_from_written_event(monkeypatch):
    called = {}

    monkeypatch.setattr(
        jobs_trigger.location_service,
        "_worker_send_location",
        lambda job_id: called.setdefault("job_id", job_id),
    )

    event = types.SimpleNamespace(
        data=types.SimpleNamespace(
            after=types.SimpleNamespace(to_dict=lambda: {"type": "send_location", "status": "queued"})
        ),
        params={"jobId": "job-written-1"},
    )

    jobs_trigger.process_send_location_job.__wrapped__(event)

    assert called.get("job_id") == "job-written-1"


def test_process_send_location_job_ignores_unmatched(monkeypatch):
    monkeypatch.setattr(
        jobs_trigger.location_service,
        "_worker_send_location",
        lambda job_id: (_ for _ in ()).throw(AssertionError("Should not be called")),
    )

    event = types.SimpleNamespace(
        data={"type": "other", "status": "queued"},
        params={"jobId": "job-2"},
    )

    jobs_trigger.process_send_location_job.__wrapped__(event)


def test_process_analytics_rebuild_job_runs_worker(monkeypatch):
    called = {}

    monkeypatch.setattr(
        jobs_trigger.analytics_snapshot_service,
        "process_rebuild_job",
        lambda job_id: called.setdefault("job_id", job_id),
    )

    event = types.SimpleNamespace(
        data={"type": "analytics_rebuild", "status": "queued"},
        params={"jobId": "job-analytics-1"},
    )

    jobs_trigger.process_analytics_rebuild_job.__wrapped__(event)

    assert called.get("job_id") == "job-analytics-1"


def test_process_analytics_rebuild_job_runs_worker_from_written_event(monkeypatch):
    called = {}

    monkeypatch.setattr(
        jobs_trigger.analytics_snapshot_service,
        "process_rebuild_job",
        lambda job_id: called.setdefault("job_id", job_id),
    )

    event = types.SimpleNamespace(
        data=types.SimpleNamespace(
            after=types.SimpleNamespace(to_dict=lambda: {"type": "analytics_rebuild", "status": "queued"})
        ),
        params={"jobId": "job-analytics-2"},
    )

    jobs_trigger.process_analytics_rebuild_job.__wrapped__(event)

    assert called.get("job_id") == "job-analytics-2"


def test_process_analytics_rebuild_job_ignores_unmatched(monkeypatch):
    monkeypatch.setattr(
        jobs_trigger.analytics_snapshot_service,
        "process_rebuild_job",
        lambda _job_id: (_ for _ in ()).throw(AssertionError("Should not be called")),
    )

    event = types.SimpleNamespace(
        data={"type": "send_location", "status": "queued"},
        params={"jobId": "job-analytics-3"},
    )

    jobs_trigger.process_analytics_rebuild_job.__wrapped__(event)
