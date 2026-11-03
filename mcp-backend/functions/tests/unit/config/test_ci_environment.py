import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[5]


def _guard():
    spec = importlib.util.spec_from_file_location("ci_environment",ROOT / "scripts/ci/assert-safe-environment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_ci_environment


@pytest.mark.parametrize("patch", [
    {"MCP_ENV":"production"},
    {"GCLOUD_PROJECT":"mcp-website-2a1ad"},
    {"STORAGE_BUCKET":"mcp-website-dev-39539.appspot.com"},
    {"GOOGLE_APPLICATION_CREDENTIALS":"SENTINEL_PATH"},
    {"FIREBASE_SERVICE_ACCOUNT_JSON":"SENTINEL_JSON"},
    {"PAYPAL_MODE":"live"},
    {"SENDER_API_KEY":"SENTINEL_KEY"},
    {"GCLOUD_PROJECT":""},
])
def test_ci_guard_rejects_cloud_configuration_without_values(patch):
    with pytest.raises(ValueError) as error:
        _guard()({"MCP_ENV":"test","GCLOUD_PROJECT":"demo-mcp-test",**patch})
    assert "SENTINEL" not in str(error.value)


def test_ci_guard_accepts_explicit_demo_identity():
    assert _guard()({"MCP_ENV":"test","GCLOUD_PROJECT":"demo-mcp-test"}) is None
