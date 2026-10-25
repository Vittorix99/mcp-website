import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[5]


def _guard():
    spec = importlib.util.spec_from_file_location("runtime_guard", ROOT / "scripts/lib/runtime_guard.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("patch", [
    {"GCLOUD_PROJECT":"mcp-website-2a1ad"},
    {"STORAGE_BUCKET":"mcp-website-dev-39539.appspot.com"},
    {"BACKEND_URL":"https://cloud.example.com"},
    {"GOOGLE_APPLICATION_CREDENTIALS":"/sentinel/credential.json"},
    {"FIRESTORE_EMULATOR_HOST":""},
    {"PAYPAL_MODE":"live"},
])
def test_local_commands_reject_unsafe_inputs_without_echoing_values(patch):
    with pytest.raises(ValueError) as error:
        _guard().validate_command_environment("test-unit", patch)
    assert "sentinel" not in str(error.value)


@pytest.mark.parametrize("command", ["dev-local", "test-unit", "test-emulators"])
def test_safe_dry_runs_show_demo_identity_without_cloud_credentials(command):
    result = subprocess.run([sys.executable,str(ROOT / "scripts/lib/runtime_guard.py"),command,"--dry-run"],
        env={"PATH":str(Path(sys.executable).parent)},text=True,capture_output=True,cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert "demo-mcp-" in result.stdout
    assert "mcp-website-2a1ad" not in result.stdout
    assert "credential.json" not in result.stdout


def test_legacy_production_flags_are_rejected():
    result = subprocess.run([sys.executable,str(ROOT / "scripts/lib/runtime_guard.py"),"dev-local","--env=prod"],
                            text=True,capture_output=True,cwd=ROOT)
    assert result.returncode != 0
