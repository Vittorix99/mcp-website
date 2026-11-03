import os
import subprocess
import sys

import pytest

from config.runtime_settings import RuntimeConfigurationError, load_runtime_settings
from tests.config_fixtures import cloud_environment


@pytest.mark.parametrize("key", [
    "PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "MAILERSEND_API_KEY",
    "MAILERSEND_FROM_EMAIL", "PASS2U_API_KEY", "SOUNDCLOUD_CLIENT_ID",
    "SOUNDCLOUD_CLIENT_SECRET",
])
@pytest.mark.parametrize("value", [None, "   "])
def test_active_production_provider_configuration_is_required_before_return(key, value):
    env = cloud_environment("production")
    if value is None:
        del env[key]
    else:
        env[key] = value
    with pytest.raises(RuntimeConfigurationError) as error:
        load_runtime_settings(env)
    assert key in str(error.value)
    assert "fake-" not in str(error.value)


def test_disabled_cloud_providers_need_no_credentials():
    settings = load_runtime_settings({
        "MCP_ENV": "production", "PAYPAL_CLIENT_ID": "fake-client",
        "PAYPAL_CLIENT_SECRET": "fake-secret", "MAIL_MODE": "disabled",
        "PASS2U_MODE": "disabled", "SOUNDCLOUD_MODE": "disabled",
    })
    assert settings.providers.mail_api_key is None


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_incomplete_cloud_startup_rejects_before_any_firebase_constructor(environment):
    program = '''
import firebase_admin
from firebase_admin import credentials, firestore, storage
from config.runtime_settings import RuntimeConfigurationError
def forbidden(*args, **kwargs):
    raise AssertionError("Firebase constructor called before config rejection")
credentials.ApplicationDefault = forbidden
firebase_admin.initialize_app = forbidden
firestore.client = forbidden
storage.bucket = forbidden
try:
    import main
except RuntimeConfigurationError:
    pass
else:
    raise AssertionError("Incomplete cloud startup was accepted")
'''
    env = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR") if key in os.environ}
    result = subprocess.run([sys.executable, "-c", program], env={**env, "MCP_ENV": environment},
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
