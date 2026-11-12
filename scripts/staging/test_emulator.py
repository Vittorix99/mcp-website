#!/usr/bin/env python3
"""Owner-operated bulk readback or isolated API/statistics scenarios."""
import argparse
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def build_run(*, api=False, auth=False, environ=None):
    if api and auth:
        raise ValueError("Select API or Auth scenarios, not both")
    spec = importlib.util.spec_from_file_location('synthetic_runtime_guard', ROOT / 'scripts/lib/runtime_guard.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    incoming = dict(os.environ if environ is None else environ)
    settings, env = guard.command_environment('test-emulators', {
        **incoming, 'FIRESTORE_EMULATOR_HOST': '127.0.0.1:8180',
    })
    if settings.firebase.project_id != 'demo-mcp-test':
        raise ValueError('Synthetic proof requires the dedicated demo project')
    env['FIREBASE_EMULATOR_HUB'] = '127.0.0.1:4480'
    python = str(ROOT / '.venv/bin/python')
    if api or auth:
        env['SYNTHETIC_API_TESTS'] = '1'
        env['SKIP_STORAGE_ASSET_BOOTSTRAP'] = '1'
        if auth:
            env['SYNTHETIC_AUTH_TESTS'] = '1'
            env['FIREBASE_AUTH_EMULATOR_HOST'] = '127.0.0.1:9190'
        suite = 'synthetic_auth' if auth else 'synthetic_api'
        report = 'auth-results.xml' if auth else 'api-results.xml'
        command = [python, '-m', 'pytest', '-c', str(ROOT / 'mcp-backend/functions/pytest.ini'),
                   str(ROOT / 'mcp-backend/functions/tests' / suite), '-q', '--tb=short',
                   '--junitxml=' + str(ROOT / '.local/staging' / report)]
    else:
        command = [python, str(ROOT / 'scripts/staging/load_emulator.py'),
                   '--directory', str(ROOT / '.local/staging/dataset'), '--project', 'demo-mcp-test',
                   '--host', '127.0.0.1:8180', '--hub', '127.0.0.1:4480', '--apply']
    return [str(ROOT / 'mcp-website/node_modules/.bin/firebase'), 'emulators:exec',
            '--project', 'demo-mcp-test', '--only', 'firestore,auth' if auth else 'firestore',
            '--config', str(ROOT / 'firebase.synthetic-emulator.json'), shlex.join(command)], env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--auth', action='store_true', help='Real Auth tokens and isolated Firestore ownership scenarios')
    modes.add_argument('--api', action='store_true', help='Small HTTP-handler/Firestore scenarios, not bulk import')
    args = parser.parse_args()
    command, env = build_run(api=args.api, auth=args.auth)
    (ROOT / '.local/staging').mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(ROOT / '.local/staging', 0o700)
    return subprocess.run(command, cwd=ROOT, env=env).returncode


if __name__ == '__main__':
    sys.exit(main())
