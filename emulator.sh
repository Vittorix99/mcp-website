#!/usr/bin/env bash
set -euo pipefail

# Esempi comuni:
# - Avvia solo Functions emulator usando .env.integration locale:
#   ./emulator.sh
#
# - Avvia Functions + Auth + Firestore emulator con Doppler:
#   ./emulator.sh --env=test --auth=true --firestore-emulator=true --doppler=true
#
# - Avvia Functions + Auth + Firestore importando backup runtime-data:
#   ./emulator.sh --env=test --auth=true --firestore-emulator=true --import-backup=true --doppler=true
#
# - Avvia Functions contro ambiente prod cloud, senza Firestore emulator:
#   ./emulator.sh --env=prod --doppler=true
#
# - Avvia backend con progetto/config Doppler custom:
#   ./emulator.sh --env=test --doppler=true --doppler-project=mcp-backend --doppler-config=dev_backend
#
# Nota: Firestore emulator e consentito solo con --env=test.

ENVIRONMENT="test"   # test | prod
AUTH=false
USE_FIRESTORE_EMULATOR=false
USE_PUBSUB_EMULATOR=false
PUBSUB_FLAG_SET=false
IMPORT_BACKUP=false
PROJECT_ID=""
DOPPLER=false
DOPPLER_PROJECT="${DOPPLER_PROJECT:-mcp-backend}"
DOPPLER_CONFIG="${DOPPLER_CONFIG:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DATA_DIR="$SCRIPT_DIR/runtime-data"
EXPORT_DIR="$RUNTIME_DATA_DIR/emulator-data"

usage() {
  cat <<'USAGE'
Usage: ./emulator.sh [--env=test|prod] [--firestore-emulator=true|false] [--auth=true|false] [--import-backup=true|false] [--backup-dir=PATH] [--doppler=true|false] [--doppler-project=NAME] [--doppler-config=NAME]

Examples:
  ./emulator.sh
  ./emulator.sh --env=prod
  ./emulator.sh --env=test --firestore-emulator=true
  ./emulator.sh --env=test --auth=true --firestore-emulator=true
  ./emulator.sh --env=test --auth=true 
  ./emulator.sh --env=test --auth=true --import-backup=true --backup-dir=runtime-data/emulator-data --firestore-emulator=true
  ./emulator.sh --env=test --auth=true --firestore-emulator=true --doppler=true
  ./emulator.sh --env=prod --doppler=true

Notes:
- Default environment is test (loads .env.integration).
- When --env=prod, MCP_ENV=prod is exported (loads .env).
- With --doppler=true, .env files are not loaded by the backend; Doppler is the source of truth.
- Default Doppler config is dev_backend for --env=test and prd_backend for --env=prod.
- Project ID is inferred from the Firebase service account JSON when available.
- Firestore emulator can only be enabled in test.
- Emulator data is exported on exit to runtime-data/emulator-data by default.
- Import del backup avviene solo se --import-backup=true.
USAGE
}

get_project_id() {
  local sa_file="$1"
  if [ -n "${FIREBASE_SERVICE_ACCOUNT_JSON:-}" ]; then
    python3 - <<'PY'
import json
import os

data = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
print(data.get("project_id", ""))
PY
    return
  fi
  if [ -f "$sa_file" ]; then
    python3 - <<PY
import json
with open("${sa_file}", "r", encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("project_id", ""))
PY
  fi
}

for arg in "$@"; do
  case "$arg" in
    --env=test) ENVIRONMENT="test" ;;
    --env=prod) ENVIRONMENT="prod" ;;
    --firestore-emulator=true) USE_FIRESTORE_EMULATOR=true ;;
    --firestore-emulator=false) USE_FIRESTORE_EMULATOR=false ;;
    --pubsub-emulator=true) USE_PUBSUB_EMULATOR=true; PUBSUB_FLAG_SET=true ;;
    --pubsub-emulator=false) USE_PUBSUB_EMULATOR=false; PUBSUB_FLAG_SET=true ;;
    --auth=true) AUTH=true ;;
    --auth=false) AUTH=false ;;
    --import-backup=true) IMPORT_BACKUP=true ;;
    --import-backup=false) IMPORT_BACKUP=false ;;
    --backup-dir=*) EXPORT_DIR="${arg#*=}" ;;
    --doppler=true) DOPPLER=true ;;
    --doppler=false) DOPPLER=false ;;
    --doppler-project=*) DOPPLER_PROJECT="${arg#*=}" ;;
    --doppler-config=*) DOPPLER_CONFIG="${arg#*=}" ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ -z "$DOPPLER_CONFIG" ]; then
  if [ "$ENVIRONMENT" = "prod" ]; then
    DOPPLER_CONFIG="prd_backend"
  else
    DOPPLER_CONFIG="dev_backend"
  fi
fi

if [ "$DOPPLER" = true ] && [ "${MCP_USE_DOPPLER:-}" != "1" ]; then
  if ! command -v doppler >/dev/null 2>&1; then
    echo "Doppler CLI not found. Install/login Doppler or rerun with --doppler=false." >&2
    exit 1
  fi
  exec env MCP_USE_DOPPLER=1 doppler run --project "$DOPPLER_PROJECT" --config "$DOPPLER_CONFIG" -- "$SCRIPT_DIR/emulator.sh" "$@"
fi

if [ "$ENVIRONMENT" = "prod" ]; then
  export MCP_ENV=prod
  PROJECT_ID="$(get_project_id "$SCRIPT_DIR/mcp-backend/functions/service_account.json")"
else
  export MCP_ENV=test
  PROJECT_ID="$(get_project_id "$SCRIPT_DIR/mcp-backend/functions/service_account_test.json")"
fi

if [ "$ENVIRONMENT" = "prod" ] && [ "$USE_FIRESTORE_EMULATOR" = true ]; then
  echo "Firestore emulator can only be enabled in test." >&2
  exit 1
fi

if [ "$USE_FIRESTORE_EMULATOR" = true ] && [ "$PUBSUB_FLAG_SET" = false ]; then
  USE_PUBSUB_EMULATOR=true
fi

IMPORT_FLAG=""
EXPORT_FLAG=""
if [ "$AUTH" = true ] || [ "$USE_FIRESTORE_EMULATOR" = true ] || [ "$USE_PUBSUB_EMULATOR" = true ]; then
  mkdir -p "$EXPORT_DIR"
  EXPORT_FLAG="--export-on-exit=$EXPORT_DIR"
fi

if [ "$IMPORT_BACKUP" = true ]; then
  if [ -d "$EXPORT_DIR" ] && [ -n "$(ls -A "$EXPORT_DIR" 2>/dev/null)" ]; then
    IMPORT_FLAG="--import=$EXPORT_DIR"
  else
    echo "Backup dir '$EXPORT_DIR' non trovata o vuota: import saltato."
  fi
fi

ONLY_SERVICES="functions"
if [ "$AUTH" = true ]; then
  export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
  ONLY_SERVICES="$ONLY_SERVICES,auth"
else
  unset FIREBASE_AUTH_EMULATOR_HOST
fi

if [ "$USE_FIRESTORE_EMULATOR" = true ]; then
  export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
  ONLY_SERVICES="$ONLY_SERVICES,firestore"
else
  unset FIRESTORE_EMULATOR_HOST
fi

if [ "$USE_PUBSUB_EMULATOR" = true ]; then
  export PUBSUB_EMULATOR_HOST=127.0.0.1:8085
  ONLY_SERVICES="$ONLY_SERVICES,pubsub"
else
  unset PUBSUB_EMULATOR_HOST
fi

if [ -n "$PROJECT_ID" ]; then
  firebase emulators:start --only "$ONLY_SERVICES" --project "$PROJECT_ID" $IMPORT_FLAG $EXPORT_FLAG
else
  firebase emulators:start --only "$ONLY_SERVICES" $IMPORT_FLAG $EXPORT_FLAG
fi
