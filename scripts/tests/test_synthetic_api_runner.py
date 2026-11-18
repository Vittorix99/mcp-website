"""Runner safety/command contract; these tests never launch an emulator."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('synthetic_scenario_runner', ROOT / 'scripts/staging/test_emulator.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_api_mode_selects_only_dedicated_firestore_and_offline_providers():
    command, env = runner.build_run(api=True, environ={'PATH': '/usr/bin'})
    assert command[command.index('--only') + 1] == 'firestore'
    assert command[command.index('--project') + 1] == 'demo-mcp-test'
    assert 'tests/synthetic_api' in command[-1]
    assert 'load_emulator.py' not in command[-1]
    assert env['FIRESTORE_EMULATOR_HOST'] == '127.0.0.1:8180'
    assert env['FIREBASE_EMULATOR_HUB'] == '127.0.0.1:4480'
    assert env['SYNTHETIC_API_TESTS'] == '1'
    assert env['PAYPAL_MODE'] == 'fake'
    assert env['MAIL_MODE'] in {'fake', 'disabled'}
    assert env['SENDER_MODE'] == 'disabled'
    assert 'GOOGLE_APPLICATION_CREDENTIALS' not in env


def test_import_mode_still_selects_bulk_import_and_not_api_suite():
    command, env = runner.build_run(api=False, environ={'PATH': '/usr/bin'})
    assert 'load_emulator.py' in command[-1]
    assert 'tests/synthetic_api' not in command[-1]


@pytest.mark.parametrize('incoming', [{'MCP_ENV': 'production'}, {'PAYPAL_MODE': 'live'}, {'GOOGLE_APPLICATION_CREDENTIALS': '/unused/key.json'}])
def test_api_runner_rejects_cloud_configuration(incoming):
    with pytest.raises(ValueError):
        runner.build_run(api=True, environ={'PATH': '/usr/bin', **incoming})



def test_auth_mode_selects_dedicated_auth_and_firestore_with_real_verifier_suite():
    command, env = runner.build_run(auth=True, environ={'PATH': '/usr/bin'})
    assert command[command.index('--only') + 1] == 'firestore,auth'
    assert command[command.index('--project') + 1] == 'demo-mcp-test'
    assert 'tests/synthetic_auth' in command[-1]
    assert 'auth-results.xml' in command[-1]
    assert env['FIREBASE_AUTH_EMULATOR_HOST'] == '127.0.0.1:9190'
    assert env['SYNTHETIC_AUTH_TESTS'] == '1'
    assert env['PAYPAL_MODE'] == 'fake' and env['SENDER_MODE'] == 'disabled'
    assert 'GOOGLE_APPLICATION_CREDENTIALS' not in env


def test_auth_and_api_modes_cannot_be_mixed():
    with pytest.raises(ValueError):
        runner.build_run(api=True, auth=True, environ={'PATH': '/usr/bin'})


@pytest.mark.parametrize('incoming', [{'MCP_ENV': 'production'}, {'PAYPAL_MODE': 'live'},
                                     {'GOOGLE_APPLICATION_CREDENTIALS': '/unused/key.json'}])
def test_auth_runner_rejects_cloud_configuration(incoming):
    with pytest.raises(ValueError):
        runner.build_run(auth=True, environ={'PATH': '/usr/bin', **incoming})
