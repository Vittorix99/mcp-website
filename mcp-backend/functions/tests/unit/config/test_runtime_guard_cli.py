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


def test_emulator_cli_enables_framework_support_without_saved_user_settings(monkeypatch):
    from types import SimpleNamespace

    guard = _guard()
    monkeypatch.setattr(guard.os, "environ", {})
    monkeypatch.setattr(guard, "_ensure_cli_venv", lambda: None)

    def run(command, *, cwd, env):
        assert command[1] == "emulators:exec"
        assert env.get("FIREBASE_CLI_EXPERIMENTS") == "webframeworks"
        assert env["GCLOUD_PROJECT"] == "demo-mcp-test"
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(guard.subprocess, "run", run)
    assert guard.main(["test-emulators"]) == 0


def test_local_seed_waits_for_auth_as_well_as_firestore(monkeypatch):
    import socket
    import time
    from contextlib import nullcontext
    from types import SimpleNamespace

    guard = _guard()
    settings = SimpleNamespace(firebase=SimpleNamespace(project_id="demo-mcp-local"))
    monkeypatch.setattr(guard, "command_environment", lambda *_: (settings, {}))
    monkeypatch.setattr(guard, "_ensure_cli_venv", lambda: None)
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    attempts = {8080: 0, 9099: 0}

    def connect(address, **_kwargs):
        port = address[1]
        attempts[port] += 1
        if port == 9099 and attempts[port] == 1:
            raise ConnectionRefusedError("Auth is still starting")
        return nullcontext()

    monkeypatch.setattr(socket, "create_connection", connect)

    class Child:
        returncode = 0

        def poll(self):
            return 0

        def wait(self, **_kwargs):
            return 0

    monkeypatch.setattr(guard.subprocess, "Popen", lambda *_args, **_kwargs: Child())

    def seed(_env, seed=False):
        assert seed
        assert attempts[9099] == 2, "Seed must wait until Auth accepts connections"
        return 0

    monkeypatch.setattr(guard, "_inside_emulators", seed)
    assert guard.main(["dev-local", "--seed"]) == 0
