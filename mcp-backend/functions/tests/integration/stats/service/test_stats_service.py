import pytest

from services.stats_service import StatsService


@pytest.mark.integration
def test_stats_service_general_stats(create_stats_fixtures):
    """Computes general stats from Firestore."""
    create_stats_fixtures()
    service = StatsService()
    stats = service.get_general_stats()

    assert stats.get("total_events", 0) >= 1
    assert stats.get("total_purchases", 0) >= 1
    assert stats.get("total_active_members", 0) >= 1
    assert stats.get("last_24h_unanswered_messages", 0) >= 1
    assert stats.get("last_message") is not None
    assert stats.get("last_membership") is not None
    assert stats.get("last_purchase") is not None
    assert stats.get("last_participant") is not None
