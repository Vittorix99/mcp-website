#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$SCRIPT_DIR/secrets_manifest.conf"
PROJECT="${DOPPLER_PROJECT:-}"
CONFIG="${DOPPLER_CONFIG:-}"
ENVIRONMENT="${DOPPLER_ENVIRONMENT:-}"
SCOPE=""
DRY_RUN=false

usage() {
  cat <<'USAGE'
Usage: scripts/doppler/push_secrets.sh --project=PROJECT --config=DOPPLER_CONFIG --scope=backend|frontend [--env=dev|prod] [--manifest=PATH] [--dry-run]

Importa su Doppler le variabili reali, non file base64.
I file .env sorgente vengono parsati in KEY=VALUE separati; i service account JSON vengono salvati come JSON grezzo in una singola variabile.

Examples:
  scripts/doppler/push_secrets.sh --project=mcp-backend --config=dev_backend --scope=backend --env=dev
  scripts/doppler/push_secrets.sh --project=mcp-frontend --config=prd_frontend --scope=frontend --env=prod
  DOPPLER_PROJECT=mcp-backend DOPPLER_CONFIG=dev_backend scripts/doppler/push_secrets.sh --scope=backend
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
    --dry-run) DRY_RUN=true ;;
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

if [ ! -f "$MANIFEST" ]; then
  echo "Manifest not found: $MANIFEST" >&2
  exit 1
fi

TMP_JSON="$(mktemp)"
trap 'rm -f "$TMP_JSON"' EXIT

# Il parsing avviene in Python per evitare problemi con quote, spazi e valori che contengono '='.
REPO_ROOT="$REPO_ROOT" MANIFEST="$MANIFEST" SCOPE="$SCOPE" ENVIRONMENT="$ENVIRONMENT" OUTPUT_JSON="$TMP_JSON" python3 - <<'PY'
import json
import os
import shlex
import sys
from pathlib import Path

repo_root = Path(os.environ["REPO_ROOT"])
manifest = Path(os.environ["MANIFEST"])
scope = os.environ["SCOPE"]
environment = os.environ["ENVIRONMENT"]
output_json = Path(os.environ["OUTPUT_JSON"])

secrets: dict[str, str] = {}
source_count = 0
missing_count = 0


def parse_env_file(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            print(f"skip invalid env line: {path}:{line_number}", file=sys.stderr)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.replace("_", "").isalnum() or key[0].isdigit():
            print(f"invalid secret name in {path}:{line_number}: {key}", file=sys.stderr)
            sys.exit(1)

        # shlex rimuove quote esterne e interpreta escaping standard senza valutare variabili di shell.
        try:
            tokens = shlex.split(value, comments=False, posix=True)
            parsed[key] = tokens[0] if len(tokens) == 1 else value
        except ValueError:
            parsed[key] = value.strip()
    return parsed


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

    source = repo_root / rel_path
    if not source.exists():
        print(f"skip missing: {rel_path}", file=sys.stderr)
        missing_count += 1
        continue

    if kind == "env_target":
        continue
    if kind == "env_source":
        parsed = parse_env_file(source)
        for key, value in parsed.items():
            if key in secrets:
                print(f"override secret from later env file: {key}", file=sys.stderr)
            secrets[key] = value
        print(f"prepared env file: {rel_path} ({len(parsed)} secrets)", file=sys.stderr)
        source_count += 1
    elif kind == "json_file":
        if not secret_name:
            print(f"Missing secret_name for json_file: {raw_line}", file=sys.stderr)
            sys.exit(1)
        # Validiamo JSON, ma carichiamo il contenuto originale: Doppler avra la variabile JSON leggibile.
        json.loads(source.read_text(encoding="utf-8"))
        secrets[secret_name] = source.read_text(encoding="utf-8").strip()
        print(f"prepared json file: {rel_path} -> {secret_name}", file=sys.stderr)
        source_count += 1
    else:
        print(f"Unsupported manifest kind: {kind}", file=sys.stderr)
        sys.exit(1)

if not secrets:
    print("No secrets found for selected scope/config. Nothing uploaded.", file=sys.stderr)
    sys.exit(1)

output_json.write_text(json.dumps(secrets, indent=2, sort_keys=True), encoding="utf-8")
print(f"Prepared {len(secrets)} secrets from {source_count} sources. Skipped {missing_count} missing sources.", file=sys.stderr)
PY

if [ "$DRY_RUN" = true ]; then
  echo "Dry run: upload not executed for project=$PROJECT config=$CONFIG scope=$SCOPE env=$ENVIRONMENT." >&2
  exit 0
fi

if ! command -v doppler >/dev/null 2>&1; then
  echo "Doppler CLI not found. Install and authenticate it before running this script." >&2
  exit 1
fi

doppler secrets upload "$TMP_JSON" --project "$PROJECT" --config "$CONFIG"
echo "Uploaded Doppler secrets to project=$PROJECT config=$CONFIG scope=$SCOPE env=$ENVIRONMENT." >&2
