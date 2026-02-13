import pytest

from api.admin import stats_api
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
