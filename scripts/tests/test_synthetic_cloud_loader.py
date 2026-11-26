import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/staging'))
spec = importlib.util.spec_from_file_location('load_cloud', ROOT / 'scripts/staging/load_cloud.py')
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)

GOOD = {'type': 'authorized_user', 'client_id': 'x', 'client_secret': 'y', 'refresh_token': 'z',
        'quota_project_id': loader.PROJECT}


def write(tmp_path, data, mode=0o600):
    path = tmp_path / 'adc.json'
    path.write_text(json.dumps(data))
    path.chmod(mode)
    return path


def test_private_personal_staging_credential_is_accepted(tmp_path):
    assert loader.validate_credential(write(tmp_path, GOOD), {}) == tmp_path / 'adc.json'


@pytest.mark.parametrize('change', [
    {'quota_project_id': 'mcp-website-2a1ad'}, {'quota_project_id': None}, {'type': 'service_account'},
    {'private_key': 'k'}, {'service_account_impersonation_url': 'u'},
])
def test_wrong_credential_is_rejected(tmp_path, change):
    with pytest.raises(ValueError):
        loader.validate_credential(write(tmp_path, {**GOOD, **change}), {})


def test_group_readable_credential_and_emulator_host_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        loader.validate_credential(write(tmp_path, GOOD, 0o640), {})
    with pytest.raises(ValueError):
        loader.validate_credential(write(tmp_path, GOOD), {'FIRESTORE_EMULATOR_HOST': '127.0.0.1:8080'})


def test_relative_credential_is_rejected(tmp_path, monkeypatch):
    write(tmp_path, GOOD)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        loader.validate_credential('adc.json', {})
