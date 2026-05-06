from models import AnalyticsJob, Job, LocationJob


def test_location_job_extends_base_job_with_location_fields():
    job = LocationJob(event_id="event-1", address="Via Roma", link="https://maps.example", message="Ingresso A")
    payload = job.to_firestore(include_none=False)

    assert isinstance(job, Job)
    assert payload["type"] == "send_location"
    assert payload["event_id"] == "event-1"
    assert payload["address"] == "Via Roma"
    assert payload["link"] == "https://maps.example"
    assert payload["message"] == "Ingresso A"
    assert payload["total"] == 0
    assert payload["sent"] == 0
    assert "scope" not in payload


def test_analytics_job_extends_base_job_with_analytics_fields():
    job = AnalyticsJob(scope="event", target_event_id="event-1", reason="manual:admin")
    payload = job.to_firestore(include_none=False)

    assert isinstance(job, Job)
    assert payload["type"] == "analytics_rebuild"
    assert payload["target_event_id"] == "event-1"
    assert payload["scope"] == "event"
    assert payload["reason"] == "manual:admin"
    assert "address" not in payload
    assert "message" not in payload
    assert "total" not in payload
    assert "sent" not in payload
