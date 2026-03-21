import pytest

from api.admin import setting_api
from tests.utils import DummyRequest, unwrap_response


@pytest.mark.integration
def test_settings_api_set_get(settings_repository, setting_key):
    """Sets and retrieves settings via API endpoints."""
    try:
        set_req = DummyRequest(method="POST", json={"key": setting_key, "value": "value-2"})
        resp, status = unwrap_response(setting_api.set_settings(set_req))
        assert status == 200
        assert resp.get("setting", {}).get("key") == setting_key

        get_req = DummyRequest(method="GET", args={"key": setting_key})
        resp, status = unwrap_response(setting_api.get_settings(get_req))
        assert status == 200
        assert resp.get("key") == setting_key
    finally:
        settings_repository.collection.document(setting_key).delete()


@pytest.mark.integration
def test_settings_api_missing_key():
    """Returns 400 when key is missing."""
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(setting_api.get_settings(req))
    assert status == 200
    assert "settings" in resp
