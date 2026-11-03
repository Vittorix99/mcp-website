import os
from pathlib import Path
import subprocess
import sys

import pytest


FUNCTIONS = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("patch", [
    {"MCP_ENV": "invalid-sentinel"},
    {"MCP_ENV": "test", "FIRESTORE_EMULATOR_HOST": ""},
    {"MCP_ENV": "local", "GOOGLE_APPLICATION_CREDENTIALS": "/sentinel/credential.json"},
])
def test_startup_validates_before_firebase_and_provider_initialization(patch):
    env = {"PATH": os.environ["PATH"], "MCP_ENV": "test", **patch}
    result = subprocess.run([sys.executable, "-c", "import main"], cwd=FUNCTIONS,
                            env=env, text=True, capture_output=True, timeout=15)
    assert result.returncode != 0
    assert "RuntimeConfigurationError" in result.stderr
    assert "sentinel" not in result.stderr
    assert "FileNotFoundError" not in result.stderr


def test_startup_summary_is_redacted():
    from config.runtime_settings import load_runtime_settings, safe_runtime_summary
    summary = safe_runtime_summary(load_runtime_settings({"MCP_ENV": "test", "SENDER_API_KEY": "SENTINEL_SECRET"}))
    assert "SENTINEL_SECRET" not in str(summary)
    assert summary["firebase_emulator"] is True
