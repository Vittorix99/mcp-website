import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[5]


def test_canonical_firebase_manifest_passes_standalone_validator():
    result = subprocess.run([sys.executable,str(ROOT / "scripts/validate-firebase-config.py")],
                            cwd=ROOT,text=True,capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout


def test_validator_rejects_nested_config_and_wrong_runtime(tmp_path):
    spec = importlib.util.spec_from_file_location("manifest_validator", ROOT / "scripts/validate-firebase-config.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    (tmp_path / "mcp-website").mkdir()
    (tmp_path / "mcp-website/firebase.json").write_text("{}")
    (tmp_path / "firebase.json").write_text(json.dumps({"functions":[{"source":"mcp-backend/functions","runtime":"python310"}]}))
    (tmp_path / ".firebaserc").write_text(json.dumps({"projects":{"default":"mcp-website-2a1ad"}}))
    failures = validator.validate(tmp_path)
    assert any("duplicate" in item.lower() for item in failures)
    assert any("runtime" in item.lower() for item in failures)
    assert any("alias" in item.lower() for item in failures)
