"""Deployment discovery must not need unrelated provider credentials."""
import importlib
from unittest.mock import Mock

import pytest

from config import runtime_settings as runtime


@pytest.fixture(autouse=True)
def reset_settings():
    runtime.clear_runtime_settings_cache()
    yield
    runtime.clear_runtime_settings_cache()


def staging(monkeypatch):
    for key in tuple(__import__('os').environ):
        if key.endswith('_MODE') or key.startswith(('PAYPAL_', 'MAILERSEND_', 'PASS2U_', 'SOUNDCLOUD_')) or key in {
            'GCLOUD_PROJECT', 'GOOGLE_CLOUD_PROJECT', 'STORAGE_BUCKET', 'FIREBASE_CONFIG',
            'BACKEND_URL', 'ALLOWED_ORIGINS', 'ADMIN_PORT', 'FUNCTION_TARGET', 'K_SERVICE',
            'FIRESTORE_EMULATOR_HOST', 'FIREBASE_AUTH_EMULATOR_HOST', 'STORAGE_EMULATOR_HOST',
            'PUBSUB_EMULATOR_HOST', 'FIREBASE_EMULATOR_HUB', 'FUNCTIONS_EMULATOR',
        }:
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('MCP_ENV', 'staging')


def test_discovery_policy_needs_no_provider_secret_but_strict_loader_still_does(monkeypatch):
    staging(monkeypatch)
    assert runtime.get_runtime_policy().firebase.project_id == 'mcp-website-dev-39539'
    with pytest.raises(runtime.RuntimeConfigurationError, match='PAYPAL_CLIENT_ID'):
        runtime.get_runtime_settings()


def test_release_requires_project_specific_runtime_identity(monkeypatch):
    from config.function_secrets import configure_runtime_identity
    from firebase_functions import options
    staging(monkeypatch)
    monkeypatch.setenv('MCP_RELEASE_SHA', 'a' * 40)
    settings = runtime.get_runtime_policy()
    for account in ['', 'runtime@wrong.iam.gserviceaccount.com']:
        monkeypatch.setenv('MCP_RUNTIME_SERVICE_ACCOUNT', account)
        with pytest.raises(runtime.RuntimeConfigurationError):
            configure_runtime_identity(settings)
    account = 'app-runtime@mcp-website-dev-39539.iam.gserviceaccount.com'
    monkeypatch.setenv('MCP_RUNTIME_SERVICE_ACCOUNT', account)
    setter = Mock()
    monkeypatch.setattr(options, 'set_global_options', setter)
    configure_runtime_identity(settings)
    setter.assert_called_once_with(service_account=account)


def test_disabled_provider_does_not_require_another_providers_secrets(monkeypatch):
    staging(monkeypatch)
    from services.communications.mail_service import build_mail_service, DisabledMailService
    assert isinstance(build_mail_service(), DisabledMailService)


def test_active_provider_requires_its_own_credentials(monkeypatch):
    staging(monkeypatch)
    with pytest.raises(runtime.RuntimeConfigurationError, match='PAYPAL_CLIENT_ID'):
        runtime.get_provider_settings('paypal')
    monkeypatch.setenv('PAYPAL_CLIENT_ID', 'public-sandbox-id')
    runtime.clear_runtime_settings_cache()
    with pytest.raises(runtime.RuntimeConfigurationError, match='PAYPAL_CLIENT_SECRET'):
        runtime.get_provider_settings('paypal')


def test_discovery_policy_still_rejects_wrong_project(monkeypatch):
    staging(monkeypatch)
    monkeypatch.setenv('GCLOUD_PROJECT', 'mcp-website-2a1ad')
    with pytest.raises(runtime.RuntimeConfigurationError, match='GCLOUD_PROJECT'):
        runtime.get_runtime_policy()


@pytest.mark.parametrize('module_name,class_name,field,builder', [
    ('services.memberships.memberships_service', 'MembershipsService', 'pass2u_service', 'build_pass2u_service'),
    ('services.memberships.merge_service', 'MergeService', 'pass2u_service', 'build_pass2u_service'),
    ('services.radio.radio_episode_service', 'RadioEpisodeService', 'soundcloud_service', 'build_soundcloud_service'),
])
def test_service_construction_defers_provider_and_preserves_injection(monkeypatch, module_name, class_name, field, builder):
    module = importlib.import_module(module_name)
    factory = Mock(return_value=object())
    monkeypatch.setattr(module, builder, factory)
    service = getattr(module, class_name)()
    factory.assert_not_called()
    assert getattr(service, field) is factory.return_value
    assert getattr(service, field) is factory.return_value
    factory.assert_called_once_with()
    injected = object()
    assert getattr(getattr(module, class_name)(**{field: injected}), field) is injected
    factory.assert_called_once_with()


def test_secret_bindings_are_scoped_to_function_and_active_provider(monkeypatch):
    staging(monkeypatch)
    from config.function_secrets import secrets_for_function
    assert [s.name for s in secrets_for_function('create_order_event')] == ['PAYPAL_CLIENT_SECRET']
    assert secrets_for_function('get_all_events') == []
    assert secrets_for_function('on_membership_created') == []


def test_production_read_endpoint_needs_no_unrelated_secrets(monkeypatch):
    staging(monkeypatch)
    monkeypatch.setenv('MCP_ENV', 'production')
    monkeypatch.setenv('FUNCTION_TARGET', 'get_all_events')
    from config.function_secrets import startup_settings, secrets_for_function
    assert startup_settings().environment is runtime.RuntimeEnvironment.PRODUCTION
    assert {s.name for s in secrets_for_function('on_membership_created')} == {'MAILERSEND_API_KEY', 'PASS2U_API_KEY'}


def test_runtime_target_missing_secret_fails_before_client_initialization(monkeypatch):
    staging(monkeypatch)
    monkeypatch.setenv('FUNCTION_TARGET', 'create_order_event')
    from config.function_secrets import startup_settings
    with pytest.raises(runtime.RuntimeConfigurationError, match='PAYPAL_CLIENT_ID'):
        startup_settings()


def test_paid_renewal_target_requires_usable_mail_credentials(monkeypatch):
    staging(monkeypatch)
    monkeypatch.setenv('MCP_ENV', 'production')
    monkeypatch.setenv('FUNCTION_TARGET', 'capture_order_event')
    for key in ['PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PASS2U_API_KEY']:
        monkeypatch.setenv(key, 'fake-deployment-fixture')
    monkeypatch.setenv('MAILERSEND_FROM_EMAIL', 'sender@example.test')
    from config.function_secrets import startup_settings
    with pytest.raises(runtime.RuntimeConfigurationError, match='MAILERSEND_API_KEY'):
        startup_settings()
    monkeypatch.setenv('MAILERSEND_API_KEY', 'fake-mail-fixture')
    assert startup_settings().environment is runtime.RuntimeEnvironment.PRODUCTION


def test_discovery_port_allows_missing_secrets_only_outside_cloud_service(monkeypatch):
    staging(monkeypatch)
    monkeypatch.setenv('ADMIN_PORT', '8087')
    from config.function_secrets import startup_settings
    assert startup_settings().firebase.project_id == 'mcp-website-dev-39539'
    monkeypatch.setenv('K_SERVICE', 'deployed-service')
    with pytest.raises(runtime.RuntimeConfigurationError, match='PAYPAL_CLIENT_ID'):
        startup_settings()


@pytest.mark.parametrize('environment', ['staging', 'production'])
def test_real_firebase_sdk_discovers_all_functions_without_provider_credentials(environment):
    import os
    from pathlib import Path
    import subprocess
    import sys
    program = r"""
import sys,types,os
from unittest.mock import MagicMock
from firebase_functions import options
from firebase_functions.private.serving import get_functions
config=types.ModuleType('config.firebase_config')
config.db=MagicMock();config.bucket=MagicMock();config.region='us-central1'
config.cors=options.CorsOptions(cors_origins='*')
sys.modules['config.firebase_config']=config
functions=get_functions()
from config.function_secrets import FUNCTION_PROVIDERS
assert set(FUNCTION_PROVIDERS)<=set(functions),set(FUNCTION_PROVIDERS)-set(functions)
assert len(functions)>120, len(functions)
assert not functions['get_all_events'].__firebase_endpoint__.secretEnvironmentVariables
assert {x['key'] for x in functions['create_order_event'].__firebase_endpoint__.secretEnvironmentVariables}=={'PAYPAL_CLIENT_SECRET'}
assert 'PAYPAL_CLIENT_SECRET' in {x['key'] for x in functions['recover_order_event'].__firebase_endpoint__.secretEnvironmentVariables}
if os.environ['MCP_ENV']=='production':
    assert 'MAILERSEND_API_KEY' in {x['key'] for x in functions['capture_order_event'].__firebase_endpoint__.secretEnvironmentVariables}
assert all('CLIENT_ID' not in x['key'] for f in functions.values() for x in (f.__firebase_endpoint__.secretEnvironmentVariables or []))
import os
assert all(f.__firebase_endpoint__.serviceAccountEmail==os.environ['MCP_RUNTIME_SERVICE_ACCOUNT'] for f in functions.values())
print('discovery_functions',len(functions))
"""
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'TMPDIR', 'DYLD_FALLBACK_LIBRARY_PATH') if k in os.environ}
    result = subprocess.run([sys.executable, '-c', program], cwd=Path(__file__).resolve().parents[3],
        env={**env, 'MCP_ENV': environment, 'ADMIN_PORT': '8087',
             'MCP_RELEASE_SHA':'a' * 40,
             'MCP_RUNTIME_SERVICE_ACCOUNT':'app-runtime@' + ('mcp-website-dev-39539' if environment == 'staging' else 'mcp-website-2a1ad') + '.iam.gserviceaccount.com'},
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('method,authenticated,expected', [('GET', True, 405), ('POST', False, 401)])
def test_rejected_http_requests_do_not_validate_provider_secrets(monkeypatch, method, authenticated, expected):
    from api.decorators import admin_endpoint
    from config import function_secrets
    from services.core import auth_service
    from flask import Flask, request
    if not authenticated:
        monkeypatch.setattr(auth_service.auth, 'verify_id_token', Mock(side_effect=ValueError('invalid')))
    validation = Mock(side_effect=AssertionError('secret lookup before auth/method rejection'))
    monkeypatch.setattr(function_secrets, 'get_provider_settings', validation)
    @admin_endpoint(methods=('POST',))
    def send_ticket(req):
        pytest.fail('handler executed')
    app = Flask('deployment-auth-boundary')
    app.add_url_rule('/send', view_func=lambda: send_ticket(request), methods=['GET', 'POST'])
    result = app.test_client().open('/send', method=method, headers={'Authorization': 'Bearer fixture'})
    assert result.status_code == expected
    validation.assert_not_called()


def test_http_missing_provider_credentials_prevents_handler_side_effect(monkeypatch):
    from api.decorators import admin_endpoint
    from config import function_secrets
    from flask import Flask, request
    validation = Mock(side_effect=runtime.RuntimeConfigurationError('missing provider credential'))
    monkeypatch.setattr(function_secrets, 'get_provider_settings', validation)
    writes = Mock()
    @admin_endpoint(methods=('POST',))
    def send_ticket(req):
        writes()
        return 'ok'
    app = Flask('deployment-secret-boundary')
    app.testing = True
    app.add_url_rule('/send', view_func=lambda: send_ticket(request), methods=['POST'])
    result = app.test_client().post('/send', headers={'Authorization': 'Bearer fixture'})
    assert result.status_code == 503
    assert result.get_json() == {'error': 'Service configuration unavailable'}
    validation.assert_called_once_with('mail')
    writes.assert_not_called()
