"""Guard and run local/test workflows with a minimal emulator-only environment."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
FUNCTIONS = ROOT / "mcp-backend/functions"
sys.path.insert(0, str(FUNCTIONS))
from config.runtime_settings import load_runtime_settings, safe_runtime_summary


def validate_command_environment(name: str, environ) -> None:
    wanted = "local" if name == "dev-local" else "test"
    if name not in {"dev-local", "test-unit", "test-emulators"}:
        raise ValueError("Unknown local/test command")
    if environ.get("MCP_ENV", wanted) != wanted:
        raise ValueError("MCP_ENV does not match selected local/test command")
    if environ.get("MCP_ENV_FILE"):
        raise ValueError("Default local/test commands do not load MCP_ENV_FILE")
    load_runtime_settings({**environ, "MCP_ENV": wanted})


def command_environment(name, incoming):
    validate_command_environment(name, incoming)
    settings = load_runtime_settings({**incoming,"MCP_ENV":"local" if name == "dev-local" else "test"})
    env = {key: incoming[key] for key in ("HOME", "TMPDIR", "LANG", "JAVA_HOME", "SystemRoot", "WINDIR") if incoming.get(key)}
    env.update({
        "PATH": str(ROOT / ".venv/bin") + os.pathsep + incoming.get("PATH", os.defpath),
        "MCP_ENV": settings.environment.value,
        "GCLOUD_PROJECT": settings.firebase.project_id,
        "GOOGLE_CLOUD_PROJECT": settings.firebase.project_id,
        "STORAGE_BUCKET": settings.firebase.storage_bucket,
        "FIRESTORE_EMULATOR_HOST": settings.firebase.firestore_emulator_host,
        "FIREBASE_AUTH_EMULATOR_HOST": settings.firebase.auth_emulator_host,
        "STORAGE_EMULATOR_HOST": settings.firebase.storage_emulator_host,
        "PUBSUB_EMULATOR_HOST": settings.firebase.pubsub_emulator_host,
        "FIREBASE_CONFIG": json.dumps({"projectId":settings.firebase.project_id,"storageBucket":settings.firebase.storage_bucket}),
        "BACKEND_URL": settings.backend_url,
        "FIREBASE_CLI_DISABLE_UPDATE_CHECK":"1", "NEXT_TELEMETRY_DISABLED":"1",
        "NO_COLOR":"1", "PYTHONUNBUFFERED":"1",
    })
    for provider in ("paypal","mail","sender","pass2u","gender","soundcloud"):
        env[provider.upper()+"_MODE"] = getattr(settings.providers,provider).value
    return settings, env


def _ensure_cli_venv():
    target = FUNCTIONS / "venv"
    expected = (ROOT / ".venv").resolve()
    if target.exists() or target.is_symlink():
        if not target.is_symlink() or target.resolve() != expected:
            raise ValueError("Existing functions/venv is preserved; Firebase CLI requires it to link to root .venv")
    else:
        target.symlink_to(Path("../../.venv"), target_is_directory=True)


def _inside_emulators(env, seed=False):
    python = str(ROOT / ".venv/bin/python")
    node = "node"
    smoke = str(ROOT / "mcp-website/scripts/emulator-smoke.mjs")
    if seed:
        return subprocess.run([node,smoke,"--seed-only"],cwd=ROOT,env=env).returncode
    result = subprocess.run([python,"-m","pytest","tests/smoke","-q"],cwd=FUNCTIONS,env=env)
    if result.returncode:
        return result.returncode
    return subprocess.run([node,smoke],cwd=ROOT,env=env).returncode


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        raise ValueError("Select dev-local, test-unit, or test-emulators")
    name, *flags = argv
    if any(flag not in {"--dry-run","--seed","--inside"} for flag in flags):
        raise ValueError("Unsupported local/test option; legacy production modes are disabled")
    settings, env = command_environment(name,os.environ)
    if "--dry-run" in flags:
        print(json.dumps(safe_runtime_summary(settings),sort_keys=True))
        return 0
    if sys.version_info[:2] != (3,11):
        raise ValueError("Use root .venv with Python 3.11")
    if name == "test-unit":
        return subprocess.run([str(ROOT / ".venv/bin/python"),"-m","pytest","tests/unit","-q"],cwd=FUNCTIONS,env=env).returncode
    if "--inside" in flags:
        return _inside_emulators(env,"--seed" in flags)
    _ensure_cli_venv()
    firebase = str(ROOT / "mcp-website/node_modules/.bin/firebase")
    common = ["--config",str(ROOT / "firebase.json"),"--only","functions,firestore,auth,storage,pubsub","--project",settings.firebase.project_id]
    if name == "test-emulators":
        inside = shlex.join([str(ROOT / ".venv/bin/python"),str(Path(__file__).resolve()),"test-emulators","--inside"])
        return subprocess.run([firebase,"emulators:exec",*common,inside],cwd=ROOT,env=env).returncode
    children = []
    try:
        children.append(subprocess.Popen([firebase,"emulators:start",*common],cwd=ROOT,env=env))
        if "--seed" in flags:
            import socket
            deadline = time.monotonic()+60
            while time.monotonic() < deadline:
                try:
                    with socket.create_connection(("127.0.0.1",8080),timeout=.2):
                        break
                except OSError:
                    time.sleep(.2)
            else:
                raise ValueError("Firestore emulator did not become ready for synthetic seed")
            if _inside_emulators(env,seed=True):
                raise ValueError("Synthetic seed failed")
        children.append(subprocess.Popen([str(ROOT / "frontend-dev.sh")],cwd=ROOT,env=env))
        while all(child.poll() is None for child in children):
            time.sleep(.2)
        return next((child.returncode for child in children if child.poll() is not None),1)
    except KeyboardInterrupt:
        return 130
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print(str(error),file=sys.stderr)
        sys.exit(2)
