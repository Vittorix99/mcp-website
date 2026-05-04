#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$SCRIPT_DIR/secrets_manifest.conf"
PROJECT="${DOPPLER_PROJECT:-}"
CONFIG="${DOPPLER_CONFIG:-}"
ENVIRONMENT="${DOPPLER_ENVIRONMENT:-}"
SCOPE=""
OVERWRITE=false
DRY_RUN=false
ALLOW_PROD_FILE=false

usage() {
  cat <<'USAGE'
Usage: scripts/doppler/pull_secrets.sh --project=PROJECT --config=DOPPLER_CONFIG --scope=backend|frontend [--env=dev|prod] [--manifest=PATH] [--overwrite] [--dry-run] [--allow-prod-file]

Ricrea file locali partendo dalle variabili Doppler reali.
Uso previsto: sviluppo locale o bootstrap di una nuova macchina.
In produzione non usare file .env: usa `doppler run -- ...` o integrazione runtime/CI.

Examples:
  scripts/doppler/pull_secrets.sh --project=mcp-backend --config=dev_backend --scope=backend --env=dev
  scripts/doppler/pull_secrets.sh --project=mcp-frontend --config=dev_frontend --scope=frontend --env=dev --overwrite
  doppler run --project mcp-backend --config prd_backend -- npm start
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --project=*) PROJECT="${arg#*=}" ;;
    --config=*) CONFIG="${arg#*=}" ;;
    --env=*) ENVIRONMENT="${arg#*=}" ;;
    --environment=*) ENVIRONMENT="${arg#*=}" ;;
    --scope=*) SCOPE="${arg#*=}" ;;
    --manifest=*) MANIFEST="${arg#*=}" ;;
    --overwrite) OVERWRITE=true ;;
    --dry-run) DRY_RUN=true ;;
    --allow-prod-file) ALLOW_PROD_FILE=true ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ -z "$PROJECT" ] || [ -z "$CONFIG" ] || [ -z "$SCOPE" ]; then
  echo "Missing project/config/scope. Use --project=... --config=dev_backend|prd_backend --scope=backend|frontend." >&2
  exit 1
fi

if [ -z "$ENVIRONMENT" ]; then
  case "$CONFIG" in
    dev|dev_*) ENVIRONMENT="dev" ;;
    prod|prod_*|prd|prd_*) ENVIRONMENT="prod" ;;
    *)
      echo "Cannot infer logical env from config '$CONFIG'. Pass --env=dev or --env=prod." >&2
      exit 1
      ;;
  esac
fi

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
  echo "Invalid env: $ENVIRONMENT. Expected dev or prod." >&2
  exit 1
fi

if [[ "$SCOPE" != "backend" && "$SCOPE" != "frontend" ]]; then
  echo "Invalid scope: $SCOPE. Expected backend or frontend." >&2
  exit 1
fi

if [[ "$ENVIRONMENT" == "prod" && "$ALLOW_PROD_FILE" != true ]]; then
  echo "Refusing to write prod secrets to local files. In production use: doppler run --project $PROJECT --config $CONFIG -- <command>" >&2
  echo "If you explicitly need a local prod restore, rerun with --allow-prod-file." >&2
  exit 1
fi

if ! command -v doppler >/dev/null 2>&1; then
  echo "Doppler CLI not found. Install and authenticate it before running this script." >&2
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 1
fi

TMP_JSON="$(mktemp)"
trap 'rm -f "$TMP_JSON"' EXIT

doppler secrets download --no-file --format json --project "$PROJECT" --config "$CONFIG" > "$TMP_JSON"

REPO_ROOT="$REPO_ROOT" MANIFEST="$MANIFEST" SECRETS_JSON="$TMP_JSON" SCOPE="$SCOPE" ENVIRONMENT="$ENVIRONMENT" OVERWRITE="$OVERWRITE" DRY_RUN="$DRY_RUN" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

repo_root = Path(os.environ["REPO_ROOT"])
manifest = Path(os.environ["MANIFEST"])
secrets_json = Path(os.environ["SECRETS_JSON"])
scope = os.environ["SCOPE"]
environment = os.environ["ENVIRONMENT"]
overwrite = os.environ["OVERWRITE"].lower() == "true"
dry_run = os.environ["DRY_RUN"].lower() == "true"

secrets = json.loads(secrets_json.read_text(encoding="utf-8"))
written = 0
skipped_existing = 0
missing = 0


def env_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
    return f'"{escaped}"'


json_secret_names: set[str] = set()
for raw_line in manifest.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    try:
        kind, entry_scope, entry_config, _rel_path, secret_name = line.split("|", 4)
    except ValueError:
        print(f"Invalid manifest line: {raw_line}", file=sys.stderr)
        sys.exit(1)
    if entry_scope == scope and entry_config == environment and kind == "json_file" and secret_name:
        json_secret_names.add(secret_name)


for raw_line in manifest.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    try:
        kind, entry_scope, entry_config, rel_path, secret_name = line.split("|", 4)
    except ValueError:
        print(f"Invalid manifest line: {raw_line}", file=sys.stderr)
        sys.exit(1)
    if entry_scope != scope or entry_config != environment:
        continue

    target = repo_root / rel_path
    if target.exists() and not overwrite:
        print(f"skip existing: {rel_path}", file=sys.stderr)
        skipped_existing += 1
        continue

    if kind == "env_source":
        continue
    if kind == "env_target":
        keys = sorted(key for key in secrets.keys() if key not in json_secret_names)
        lines: list[str] = []
        for key in keys:
            if key not in secrets:
                print(f"missing in Doppler: {key} -> {rel_path}", file=sys.stderr)
                missing += 1
                continue
            lines.append(f"{key}={env_quote(str(secrets[key]))}")

        print(f"{'would write' if dry_run else 'write'} env file: {rel_path} ({len(lines)} secrets)", file=sys.stderr)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written += 1
    elif kind == "json_file":
        if secret_name not in secrets:
            print(f"missing in Doppler: {secret_name} -> {rel_path}", file=sys.stderr)
            missing += 1
            continue
        value = str(secrets[secret_name]).strip()
        json.loads(value)

        print(f"{'would write' if dry_run else 'write'} json file: {secret_name} -> {rel_path}", file=sys.stderr)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value + "\n", encoding="utf-8")
        written += 1
    else:
        print(f"Unsupported manifest kind: {kind}", file=sys.stderr)
        sys.exit(1)

print(f"Processed {written} files. Skipped existing {skipped_existing}. Missing secrets/templates {missing}.", file=sys.stderr)
if missing:
    sys.exit(2)
PY
